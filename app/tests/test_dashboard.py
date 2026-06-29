"""
Pruebas unitarias del Sprint 3 — Dashboard Administrativo (HU07, HU08).
Cubre TD1-TD5: resumen, gráficos y usuarios con devoluciones vencidas.
"""
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.borrower  # noqa: F401
import app.models.equipment  # noqa: F401
import app.models.loan  # noqa: F401

from app.models.borrower import Borrower
from app.models.equipment import Equipment
from app.models.loan import Loan
from database import Base, get_db
from main import app

# ── Base de datos en memoria para tests ──────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Sesión directa para insertar datos de setup."""
    db = TestingSessionLocal()
    yield db
    db.close()


# ── Constantes de fecha ───────────────────────────────────────────────────────

PAST_DATE = date(2020, 1, 1)    # Siempre vencida
FUTURE_DATE = date(2099, 12, 31)  # Nunca vencida
TODAY = date.today()


# ── Helpers de inserción directa en BD ───────────────────────────────────────

def _insert_equipment(db, code: str, status: str = "DISPONIBLE") -> Equipment:
    equip = Equipment(
        code=code,
        name=f"Equipo {code}",
        category="Computadora",
        description=None,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(equip)
    db.commit()
    db.refresh(equip)
    return equip


def _insert_borrower(db, dni: str, full_name: str = None) -> Borrower:
    borrower = Borrower(
        dni=dni,
        full_name=full_name or f"User {dni}",
        email=f"{dni}@test.com",
        phone="555-0000",
        department="IT",
        created_at=datetime.utcnow(),
    )
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def _insert_loan(
    db,
    equipment_id: int,
    borrower_id: int,
    loan_date: date = TODAY,
    due_date: date = FUTURE_DATE,
    return_date: date = None,
    status: str = "ACTIVO",
) -> Loan:
    loan = Loan(
        equipment_id=equipment_id,
        borrower_id=borrower_id,
        loan_date=loan_date,
        due_date=due_date,
        return_date=return_date,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


# ── Tests: Resumen general ────────────────────────────────────────────────────

class TestResumenGeneral:
    """HU07 — Estadísticas generales del sistema."""

    def test_TD2_resumen_sin_datos_devuelve_ceros(self, client):
        """TD2: Base vacía → todos los contadores en cero, status 200."""
        response = client.get("/dashboard/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_equipment"] == 0
        assert data["available_equipment"] == 0
        assert data["loaned_equipment"] == 0
        assert data["overdue_loans"] == 0
        assert data["overdue_borrowers"] == 0

    def test_TD1_resumen_con_datos_devuelve_metricas_correctas(
        self, client, db_session
    ):
        """TD1: Resumen refleja exactamente el estado real de la base."""
        # 3 equipos: 2 disponibles, 1 prestado
        eq1 = _insert_equipment(db_session, "EQ-01", "DISPONIBLE")
        eq2 = _insert_equipment(db_session, "EQ-02", "DISPONIBLE")
        eq3 = _insert_equipment(db_session, "EQ-03", "PRESTADO")

        b1 = _insert_borrower(db_session, "11111111")
        b2 = _insert_borrower(db_session, "22222222")

        # Préstamo vigente (due_date futuro) → no vencido
        _insert_loan(db_session, eq1.id, b1.id, TODAY, FUTURE_DATE)

        # Préstamo vencido (due_date pasado, sin return_date)
        _insert_loan(db_session, eq3.id, b2.id, PAST_DATE, PAST_DATE)

        # Préstamo devuelto (return_date registrado) → no cuenta como vencido
        _insert_loan(
            db_session, eq2.id, b1.id, PAST_DATE, PAST_DATE,
            return_date=TODAY, status="DEVUELTO",
        )

        response = client.get("/dashboard/summary")
        assert response.status_code == 200
        data = response.json()

        assert data["total_equipment"] == 3
        assert data["available_equipment"] == 2
        assert data["loaned_equipment"] == 1
        assert data["overdue_loans"] == 1
        assert data["overdue_borrowers"] == 1

    def test_mismo_borrower_multiples_vencidos_cuenta_una_vez(
        self, client, db_session
    ):
        """Un borrower con dos préstamos vencidos se cuenta una sola vez."""
        eq1 = _insert_equipment(db_session, "EQ-01", "PRESTADO")
        eq2 = _insert_equipment(db_session, "EQ-02", "PRESTADO")
        b1 = _insert_borrower(db_session, "11111111")

        _insert_loan(db_session, eq1.id, b1.id, PAST_DATE, PAST_DATE)
        _insert_loan(db_session, eq2.id, b1.id, PAST_DATE, PAST_DATE)

        data = client.get("/dashboard/summary").json()

        assert data["overdue_loans"] == 2
        assert data["overdue_borrowers"] == 1  # mismo borrower, no duplica

    def test_devuelto_con_due_date_pasado_no_cuenta_como_vencido(
        self, client, db_session
    ):
        """return_date registrado excluye el préstamo del conteo de vencidos."""
        eq1 = _insert_equipment(db_session, "EQ-01", "DISPONIBLE")
        b1 = _insert_borrower(db_session, "11111111")

        _insert_loan(
            db_session, eq1.id, b1.id, PAST_DATE, PAST_DATE,
            return_date=TODAY, status="DEVUELTO",
        )

        data = client.get("/dashboard/summary").json()

        assert data["overdue_loans"] == 0
        assert data["overdue_borrowers"] == 0


# ── Tests: Gráficos ───────────────────────────────────────────────────────────

class TestGraficos:
    """HU07 — Distribución de datos para gráficos."""

    def test_charts_sin_datos_devuelve_ceros_en_todos_los_estados(self, client):
        """Sin datos, todos los contadores del gráfico son cero."""
        response = client.get("/dashboard/charts")

        assert response.status_code == 200
        data = response.json()
        assert data["loans_by_status"]["ACTIVO"] == 0
        assert data["loans_by_status"]["DEVUELTO"] == 0
        assert data["loans_by_status"]["VENCIDO"] == 0
        assert data["equipment_by_status"]["DISPONIBLE"] == 0
        assert data["equipment_by_status"]["PRESTADO"] == 0

    def test_TD5_charts_con_datos_refleja_distribucion_correcta(
        self, client, db_session
    ):
        """TD5: La distribución de estados coincide con los datos reales."""
        eq1 = _insert_equipment(db_session, "EQ-01", "DISPONIBLE")
        eq2 = _insert_equipment(db_session, "EQ-02", "PRESTADO")
        eq3 = _insert_equipment(db_session, "EQ-03", "PRESTADO")
        b1 = _insert_borrower(db_session, "11111111")

        # 1 ACTIVO, 1 DEVUELTO, 1 VENCIDO
        _insert_loan(db_session, eq1.id, b1.id, TODAY, FUTURE_DATE, status="ACTIVO")
        _insert_loan(
            db_session, eq2.id, b1.id, PAST_DATE, PAST_DATE,
            return_date=TODAY, status="DEVUELTO",
        )
        _insert_loan(db_session, eq3.id, b1.id, PAST_DATE, PAST_DATE, status="VENCIDO")

        response = client.get("/dashboard/charts")
        assert response.status_code == 200
        data = response.json()

        # Préstamos
        assert data["loans_by_status"]["ACTIVO"] == 1
        assert data["loans_by_status"]["DEVUELTO"] == 1
        assert data["loans_by_status"]["VENCIDO"] == 1

        # Equipos
        assert data["equipment_by_status"]["DISPONIBLE"] == 1
        assert data["equipment_by_status"]["PRESTADO"] == 2

    def test_charts_incluye_todos_los_estados_aunque_sean_cero(self, client, db_session):
        """Los tres estados de préstamo siempre aparecen, incluso si alguno es cero."""
        eq1 = _insert_equipment(db_session, "EQ-01", "PRESTADO")
        b1 = _insert_borrower(db_session, "11111111")
        _insert_loan(db_session, eq1.id, b1.id, TODAY, FUTURE_DATE, status="ACTIVO")

        data = client.get("/dashboard/charts").json()

        assert "ACTIVO" in data["loans_by_status"]
        assert "DEVUELTO" in data["loans_by_status"]
        assert "VENCIDO" in data["loans_by_status"]
        assert data["loans_by_status"]["ACTIVO"] == 1
        assert data["loans_by_status"]["DEVUELTO"] == 0
        assert data["loans_by_status"]["VENCIDO"] == 0


# ── Tests: Usuarios con devoluciones vencidas ─────────────────────────────────

class TestUsuariosVencidos:
    """HU08 — Seguimiento de usuarios con devoluciones vencidas."""

    def test_TD4_overdue_users_sin_datos_devuelve_lista_vacia(self, client):
        """TD4: Sin datos, la lista de usuarios vencidos está vacía."""
        response = client.get("/dashboard/overdue-users")

        assert response.status_code == 200
        assert response.json() == []

    def test_TD3_overdue_users_devuelve_registro_completo(
        self, client, db_session
    ):
        """TD3: Cada registro contiene todos los campos mínimos requeridos."""
        overdue_date = date(2023, 6, 15)
        eq1 = _insert_equipment(db_session, "EQ-01", "PRESTADO")
        b1 = _insert_borrower(db_session, "99999999", full_name="Carlos Mendoza")

        _insert_loan(
            db_session, eq1.id, b1.id,
            loan_date=date(2023, 6, 1),
            due_date=overdue_date,
            status="ACTIVO",
        )

        response = client.get("/dashboard/overdue-users")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        record = data[0]

        # Campos mínimos requeridos por la especificación
        assert record["borrower_full_name"] == "Carlos Mendoza"
        assert record["borrower_dni"] == "99999999"
        assert record["equipment_name"] == "Equipo EQ-01"
        assert record["due_date"] == overdue_date.isoformat()
        assert record["days_overdue"] > 0
        assert "loan_status" in record
        assert "loan_id" in record

    def test_prestamos_devueltos_excluidos_de_vencidos(self, client, db_session):
        """Préstamos con return_date NO aparecen en usuarios vencidos."""
        eq1 = _insert_equipment(db_session, "EQ-01", "DISPONIBLE")
        b1 = _insert_borrower(db_session, "88888888")

        _insert_loan(
            db_session, eq1.id, b1.id, PAST_DATE, PAST_DATE,
            return_date=TODAY, status="DEVUELTO",
        )

        response = client.get("/dashboard/overdue-users")
        assert response.status_code == 200
        assert response.json() == []

    def test_prestamos_vigentes_excluidos_de_vencidos(self, client, db_session):
        """Préstamos con due_date futuro NO aparecen en usuarios vencidos."""
        eq1 = _insert_equipment(db_session, "EQ-01", "PRESTADO")
        b1 = _insert_borrower(db_session, "77777777")

        _insert_loan(db_session, eq1.id, b1.id, TODAY, FUTURE_DATE, status="ACTIVO")

        response = client.get("/dashboard/overdue-users")
        assert response.status_code == 200
        assert response.json() == []

    def test_multiples_usuarios_vencidos_todos_aparecen(self, client, db_session):
        """Múltiples usuarios con vencimientos distintos aparecen todos."""
        eq1 = _insert_equipment(db_session, "EQ-01", "PRESTADO")
        eq2 = _insert_equipment(db_session, "EQ-02", "PRESTADO")
        b1 = _insert_borrower(db_session, "11111111", "Ana Ruiz")
        b2 = _insert_borrower(db_session, "22222222", "Luis Torres")

        _insert_loan(db_session, eq1.id, b1.id, PAST_DATE, PAST_DATE)
        _insert_loan(db_session, eq2.id, b2.id, PAST_DATE, date(2023, 3, 1))

        response = client.get("/dashboard/overdue-users")
        data = response.json()

        assert len(data) == 2
        dnis = {record["borrower_dni"] for record in data}
        assert "11111111" in dnis
        assert "22222222" in dnis
