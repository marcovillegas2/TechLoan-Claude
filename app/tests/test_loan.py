"""
Pruebas unitarias del Sprint 2 — Módulo Loan (HU04, HU05, HU06).
Cubre TL1-TL7: préstamos, devoluciones y disponibilidad.
"""
from datetime import datetime

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
    """Sesión directa para insertar datos de setup sin pasar por la API."""
    db = TestingSessionLocal()
    yield db
    db.close()


# ── Helpers de setup directo en BD ────────────────────────────────────────────

def _insert_equipment(db, code: str = "EQ-001", status: str = "DISPONIBLE") -> Equipment:
    equipment = Equipment(
        code=code,
        name=f"Equipo {code}",
        category="Computadora",
        description=None,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


def _insert_borrower(db, dni: str = "12345678") -> Borrower:
    borrower = Borrower(
        dni=dni,
        full_name="Test User",
        email=f"{dni}@example.com",
        phone="555-0000",
        department="IT",
        created_at=datetime.utcnow(),
    )
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def _loan_payload(equipment_id: int, borrower_id: int, **overrides) -> dict:
    base = {
        "equipment_id": equipment_id,
        "borrower_id": borrower_id,
        "loan_date": "2025-06-01",
        "due_date": "2025-06-15",
        "status": "ACTIVO",
    }
    base.update(overrides)
    return base


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRegistrarPrestamo:
    """HU04 — Registrar préstamos."""

    def test_TL1_prestamo_con_equipo_disponible_y_borrower_existente(
        self, client, db_session
    ):
        """TL1: Préstamo válido se crea con 201 y equipo pasa a PRESTADO."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        response = client.post(
            "/loans/", json=_loan_payload(equip.id, borrower.id)
        )

        assert response.status_code == 201
        data = response.json()
        assert data["equipment_id"] == equip.id
        assert data["borrower_id"] == borrower.id
        assert data["status"] == "ACTIVO"
        assert data["return_date"] is None

        # Verificar que el equipo cambió a PRESTADO
        equip_resp = client.get(f"/equipment/{equip.id}")
        assert equip_resp.json()["status"] == "PRESTADO"

    def test_TL2_prestamo_con_equipo_no_disponible(self, client, db_session):
        """TL2: Equipo en estado PRESTADO rechaza nuevo préstamo con 409."""
        equip = _insert_equipment(db_session, status="PRESTADO")
        borrower = _insert_borrower(db_session)

        response = client.post(
            "/loans/", json=_loan_payload(equip.id, borrower.id)
        )

        assert response.status_code == 409
        assert "disponible" in response.json()["detail"].lower()

    def test_TL3_prestamo_con_borrower_inexistente(self, client, db_session):
        """TL3: Borrower que no existe rechaza el préstamo con 404."""
        equip = _insert_equipment(db_session)

        response = client.post(
            "/loans/", json=_loan_payload(equip.id, borrower_id=9999)
        )

        assert response.status_code == 404

    def test_TL4_prestamo_con_fecha_limite_invalida(self, client, db_session):
        """TL4: due_date <= loan_date rechaza el préstamo con 422."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        # due_date antes de loan_date
        response = client.post(
            "/loans/",
            json=_loan_payload(
                equip.id,
                borrower.id,
                loan_date="2025-06-15",
                due_date="2025-06-01",
            ),
        )
        assert response.status_code == 422

        # due_date igual a loan_date
        response_equal = client.post(
            "/loans/",
            json=_loan_payload(
                equip.id,
                borrower.id,
                loan_date="2025-06-10",
                due_date="2025-06-10",
            ),
        )
        assert response_equal.status_code == 422

    def test_prestamo_con_equipo_inexistente_devuelve_404(
        self, client, db_session
    ):
        """Equipo que no existe rechaza el préstamo con 404."""
        borrower = _insert_borrower(db_session)

        response = client.post(
            "/loans/", json=_loan_payload(equipment_id=9999, borrower_id=borrower.id)
        )

        assert response.status_code == 404


class TestRegistrarDevolucion:
    """HU05 — Registrar devoluciones."""

    def test_TL5_devolucion_de_prestamo_activo(self, client, db_session):
        """TL5: Devolver préstamo activo responde 200, actualiza estado y equipo."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        loan_id = client.post(
            "/loans/", json=_loan_payload(equip.id, borrower.id)
        ).json()["id"]

        response = client.post(f"/loans/{loan_id}/return")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DEVUELTO"
        assert data["return_date"] is not None

        # Equipo debe volver a DISPONIBLE
        equip_resp = client.get(f"/equipment/{equip.id}")
        assert equip_resp.json()["status"] == "DISPONIBLE"

    def test_TL6_devolucion_de_prestamo_ya_devuelto(self, client, db_session):
        """TL6: Devolver un préstamo ya devuelto se rechaza con 409."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        loan_id = client.post(
            "/loans/", json=_loan_payload(equip.id, borrower.id)
        ).json()["id"]

        # Primera devolución
        client.post(f"/loans/{loan_id}/return")

        # Segunda devolución debe fallar
        response = client.post(f"/loans/{loan_id}/return")

        assert response.status_code == 409
        assert "ACTIVO" in response.json()["detail"]

    def test_devolucion_de_prestamo_inexistente_devuelve_404(self, client):
        """Devolver préstamo que no existe devuelve 404."""
        response = client.post("/loans/999/return")
        assert response.status_code == 404


class TestDisponibilidadEquipos:
    """HU06 — Consultar disponibilidad de equipos."""

    def test_TL7_listar_equipos_disponibles(self, client, db_session):
        """TL7: GET /loans/available-equipment devuelve solo equipos DISPONIBLES."""
        # Tres equipos: dos disponibles, uno prestado después del préstamo
        eq_a = _insert_equipment(db_session, code="EQ-A")
        eq_b = _insert_equipment(db_session, code="EQ-B")
        eq_c = _insert_equipment(db_session, code="EQ-C")
        borrower = _insert_borrower(db_session)

        # Prestar EQ-B
        client.post("/loans/", json=_loan_payload(eq_b.id, borrower.id))

        response = client.get("/loans/available-equipment")

        assert response.status_code == 200
        available_ids = [e["id"] for e in response.json()]

        assert eq_a.id in available_ids
        assert eq_c.id in available_ids
        assert eq_b.id not in available_ids  # fue prestado

    def test_available_equipment_vacio_cuando_todos_prestados(
        self, client, db_session
    ):
        """Si todos los equipos están prestados, la lista está vacía."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        client.post("/loans/", json=_loan_payload(equip.id, borrower.id))

        response = client.get("/loans/available-equipment")
        assert response.status_code == 200
        assert response.json() == []

    def test_listar_prestamos(self, client, db_session):
        """Listar préstamos devuelve 200 con registros correctos."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        client.post("/loans/", json=_loan_payload(equip.id, borrower.id))

        response = client.get("/loans/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_obtener_prestamo_por_id(self, client, db_session):
        """Obtener préstamo por id devuelve 200."""
        equip = _insert_equipment(db_session)
        borrower = _insert_borrower(db_session)

        loan_id = client.post(
            "/loans/", json=_loan_payload(equip.id, borrower.id)
        ).json()["id"]

        response = client.get(f"/loans/{loan_id}")
        assert response.status_code == 200
        assert response.json()["id"] == loan_id

    def test_obtener_prestamo_inexistente_devuelve_404(self, client):
        """Obtener préstamo que no existe devuelve 404."""
        response = client.get("/loans/9999")
        assert response.status_code == 404
