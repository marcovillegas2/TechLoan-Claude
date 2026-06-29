"""
Pruebas unitarias del Sprint 2 — Módulo Borrower (HU04 soporte).
Cubre TB1-TB4: registrar, rechazar duplicado, rechazar campo faltante, actualizar.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.borrower  # noqa: F401
import app.models.equipment  # noqa: F401
import app.models.loan  # noqa: F401

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


# ── Helper ────────────────────────────────────────────────────────────────────

def borrower_payload(**overrides) -> dict:
    base = {
        "dni": "12345678",
        "full_name": "Ana García",
        "email": "ana@example.com",
        "phone": "555-1234",
        "department": "Sistemas",
    }
    base.update(overrides)
    return base


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRegistrarSolicitante:
    """HU04 soporte — Gestión de solicitantes."""

    def test_TB1_registrar_solicitante_valido(self, client):
        """TB1: Solicitante con datos válidos se crea y responde 201."""
        response = client.post("/borrowers/", json=borrower_payload())

        assert response.status_code == 201
        data = response.json()
        assert data["dni"] == "12345678"
        assert data["full_name"] == "Ana García"
        assert data["department"] == "Sistemas"
        assert data["id"] is not None
        assert data["created_at"] is not None

    def test_TB2_registrar_solicitante_con_dni_duplicado(self, client):
        """TB2: DNI duplicado se rechaza con 409 Conflict."""
        client.post("/borrowers/", json=borrower_payload())
        response = client.post("/borrowers/", json=borrower_payload())

        assert response.status_code == 409
        assert "DNI" in response.json()["detail"] or "dni" in response.json()["detail"].lower()

    def test_TB3_registrar_solicitante_sin_campo_obligatorio(self, client):
        """TB3: Falta de campo obligatorio devuelve 422 Unprocessable Entity."""
        payload = borrower_payload()
        payload.pop("full_name")
        response = client.post("/borrowers/", json=payload)

        assert response.status_code == 422

    def test_TB3_registrar_solicitante_sin_email(self, client):
        """TB3 variante: Falta de email devuelve 422."""
        payload = borrower_payload()
        payload.pop("email")
        response = client.post("/borrowers/", json=payload)

        assert response.status_code == 422

    def test_TB4_actualizar_solicitante_valido(self, client):
        """TB4: Actualización válida de departamento responde 200."""
        borrower_id = client.post(
            "/borrowers/", json=borrower_payload()
        ).json()["id"]

        response = client.put(
            f"/borrowers/{borrower_id}",
            json={"department": "Infraestructura", "phone": "555-9999"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["department"] == "Infraestructura"
        assert data["phone"] == "555-9999"
        assert data["full_name"] == "Ana García"  # sin cambios

    def test_actualizar_solicitante_inexistente_devuelve_404(self, client):
        """Actualizar solicitante que no existe devuelve 404."""
        response = client.put("/borrowers/999", json={"department": "TI"})
        assert response.status_code == 404

    def test_actualizar_dni_duplicado_devuelve_409(self, client):
        """Actualizar con DNI ya registrado devuelve 409."""
        client.post("/borrowers/", json=borrower_payload(dni="11111111"))
        b2_id = client.post(
            "/borrowers/", json=borrower_payload(dni="22222222")
        ).json()["id"]

        response = client.put(f"/borrowers/{b2_id}", json={"dni": "11111111"})
        assert response.status_code == 409

    def test_listar_solicitantes(self, client):
        """Listar solicitantes devuelve 200 con la lista correcta."""
        client.post("/borrowers/", json=borrower_payload(dni="11111111"))
        client.post("/borrowers/", json=borrower_payload(dni="22222222"))

        response = client.get("/borrowers/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_obtener_solicitante_por_id(self, client):
        """Obtener solicitante por id devuelve 200 con los datos correctos."""
        borrower_id = client.post(
            "/borrowers/", json=borrower_payload()
        ).json()["id"]

        response = client.get(f"/borrowers/{borrower_id}")
        assert response.status_code == 200
        assert response.json()["id"] == borrower_id

    def test_obtener_solicitante_inexistente_devuelve_404(self, client):
        """Obtener solicitante que no existe devuelve 404."""
        response = client.get("/borrowers/999")
        assert response.status_code == 404
