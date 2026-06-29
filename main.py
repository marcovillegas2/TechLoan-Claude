from fastapi import FastAPI
# Añadir en main.py, justo después de la línea `from fastapi import FastAPI`

from database import Base, engine
import app.models.equipment  # noqa: F401 — registra Equipment en Base.metadata
import app.models.borrower   # noqa: F401 — registra Borrower en Base.metadata
import app.models.loan       # noqa: F401 — registra Loan en Base.metadata

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TechLoan",
    description="Sistema Administrativo de Control de Préstamos de Equipos Tecnológicos",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"status": "ok", "message": "TechLoan API is running"}

# Añadir al final de main.py
from app.controllers.equipment_controller import router as equipment_router
from app.controllers.borrower_controller import router as borrower_router
from app.controllers.loan_controller import router as loan_router
from app.controllers.dashboard_controller import router as dashboard_router

app.include_router(equipment_router)
app.include_router(borrower_router)
app.include_router(loan_router)
app.include_router(dashboard_router)