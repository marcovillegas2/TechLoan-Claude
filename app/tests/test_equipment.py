"""
Pruebas unitarias del Sprint 1 — TechLoan
Cubre HU01 (registrar), HU02 (modificar), HU03 (eliminar) equipos.
"""
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Importar modelos para registrarlos en Base.metadata ──────────────────────
import app.models.borrower  # noqa: F401
import app.models.equipment  # noqa: F401
import app.models.loan  # noqa: F401
from app.models.borrower import Borrower
from app.models.loan import Loan

from database import Base, get_db
from main import app

# ── Base de datos en memoria exclusiva para tests ────────────────────────────
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
    """Crea todas las tablas antes de cada test y las elimina al finalizar."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    """TestClient con la base de datos de prueba inyectada."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Sesión directa a la base de datos de prueba para setup de datos."""
    db = TestingSessionLocal()
    yield db
    db.close()


# ── Helper ────────────────────────────────────────────────────────────────────

def equipment_payload(**overrides) -> dict:
    base = {
        "code": "EQ-001",
        "name": "Laptop HP ProBook",
        "category": "Computadora",
        "description": "Laptop de prueba",
        "status": "DISPONIBLE",
    }
    base.update(overrides)
    return base


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRegistrarEquipo:
    """HU01 — Registrar equipos."""

    def test_T1_registrar_equipo_valido(self, client):
        """T1: Equipo con datos válidos se crea y responde 201."""
        response = client.post("/equipment/", json=equipment_payload())

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "EQ-001"
        assert data["name"] == "Laptop HP ProBook"
        assert data["status"] == "DISPONIBLE"
        assert data["id"] is not None
        assert data["created_at"] is not None

    def test_T2_registrar_equipo_con_codigo_duplicado(self, client):
        """T2: Código duplicado se rechaza con 409 Conflict."""
        client.post("/equipment/", json=equipment_payload())
        response = client.post("/equipment/", json=equipment_payload())

        assert response.status_code == 409
        assert "código" in response.json()["detail"].lower()

    def test_T3_registrar_equipo_sin_nombre(self, client):
        """T3: Equipo sin nombre se rechaza con 422 Unprocessable Entity."""
        payload = equipment_payload()
        payload.pop("name")
        response = client.post("/equipment/", json=payload)

        assert response.status_code == 422

    def test_T4_registrar_equipo_con_estado_no_permitido(self, client):
        """T4: Estado fuera del dominio se rechaza con 422."""
        response = client.post(
            "/equipment/", json=equipment_payload(status="MANTENIMIENTO")
        )

        assert response.status_code == 422


class TestModificarEquipo:
    """HU02 — Modificar equipos."""

    def test_T5_actualizar_equipo_valido(self, client):
        """T5: Actualización válida de nombre y categoría responde 200."""
        equipment_id = client.post(
            "/equipment/", json=equipment_payload()
        ).json()["id"]

        response = client.put(
            f"/equipment/{equipment_id}",
            json={"name": "Laptop Dell XPS", "category": "Portátil"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Laptop Dell XPS"
        assert data["category"] == "Portátil"
        assert data["updated_at"] is not None

    def test_actualizar_equipo_inexistente_devuelve_404(self, client):
        """Actualizar un equipo que no existe devuelve 404."""
        response = client.put("/equipment/999", json={"name": "No existe"})
        assert response.status_code == 404

    def test_actualizar_codigo_duplicado_devuelve_409(self, client):
        """Actualizar con un código ya registrado devuelve 409."""
        client.post("/equipment/", json=equipment_payload(code="EQ-001"))
        eq2_id = client.post(
            "/equipment/", json=equipment_payload(code="EQ-002")
        ).json()["id"]

        response = client.put(f"/equipment/{eq2_id}", json={"code": "EQ-001"})
        assert response.status_code == 409


class TestEliminarEquipo:
    """HU03 — Eliminar equipos."""

    def test_T6_eliminar_equipo_sin_prestamos_activos(self, client):
        """T6: Eliminar equipo sin préstamos activos responde 200 y lo retira."""
        equipment_id = client.post(
            "/equipment/", json=equipment_payload()
        ).json()["id"]

        delete_resp = client.delete(f"/equipment/{equipment_id}")
        assert delete_resp.status_code == 200

        get_resp = client.get(f"/equipment/{equipment_id}")
        assert get_resp.status_code == 404

    def test_T7_eliminar_equipo_con_prestamos_activos(self, client, db_session):
        """T7: Eliminar equipo con préstamo activo se bloquea con 409."""
        # Crear equipo vía API
        equipment_id = client.post(
            "/equipment/", json=equipment_payload()
        ).json()["id"]

        # Insertar solicitante en la BD de prueba
        borrower = Borrower(
            dni="87654321",
            full_name="Ana García",
            email="ana@example.com",
            phone="555-0000",
            department="Sistemas",
            created_at=datetime.utcnow(),
        )
        db_session.add(borrower)
        db_session.commit()
        db_session.refresh(borrower)

        # Insertar préstamo activo directamente (sin pasar por la API de préstamos)
        loan = Loan(
            equipment_id=equipment_id,
            borrower_id=borrower.id,
            loan_date=date.today(),
            due_date=date.today(),
            return_date=None,
            status="ACTIVO",
            created_at=datetime.utcnow(),
        )
        db_session.add(loan)
        db_session.commit()

        # Intentar eliminar: debe bloquearse
        response = client.delete(f"/equipment/{equipment_id}")
        assert response.status_code == 409
        assert "activos" in response.json()["detail"].lower()

    def test_eliminar_equipo_inexistente_devuelve_404(self, client):
        """Eliminar un equipo que no existe devuelve 404."""
        response = client.delete("/equipment/999")
        assert response.status_code == 404

    def test_eliminar_equipo_con_prestamos_historicos_permitido(
        self, client, db_session
    ):
        """Préstamos devueltos o vencidos no bloquean la eliminación."""
        equipment_id = client.post(
            "/equipment/", json=equipment_payload()
        ).json()["id"]

        borrower = Borrower(
            dni="11223344",
            full_name="Luis Torres",
            email="luis@example.com",
            phone="555-1111",
            department="RR.HH.",
            created_at=datetime.utcnow(),
        )
        db_session.add(borrower)
        db_session.commit()
        db_session.refresh(borrower)

        # Préstamo ya devuelto (return_date registrado, estado DEVUELTO)
        loan = Loan(
            equipment_id=equipment_id,
            borrower_id=borrower.id,
            loan_date=date.today(),
            due_date=date.today(),
            return_date=date.today(),
            status="DEVUELTO",
            created_at=datetime.utcnow(),
        )
        db_session.add(loan)
        db_session.commit()

        response = client.delete(f"/equipment/{equipment_id}")
        assert response.status_code == 200
