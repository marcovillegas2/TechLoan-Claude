from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.equipment_schema import EquipmentRead
from app.schemas.loan_schema import LoanCreate, LoanRead
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["Loans"])

_service = LoanService()


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(data: LoanCreate, db: Session = Depends(get_db)):
    return _service.create_loan(db, data)


@router.get("/", response_model=List[LoanRead], status_code=status.HTTP_200_OK)
def list_loans(db: Session = Depends(get_db)):
    return _service.list_loans(db)


# CRÍTICO: esta ruta DEBE registrarse antes de /{loan_id} para evitar que
# FastAPI intente parsear "available-equipment" como un integer de loan_id.
@router.get(
    "/available-equipment",
    response_model=List[EquipmentRead],
    status_code=status.HTTP_200_OK,
)
def get_available_equipment(db: Session = Depends(get_db)):
    return _service.get_available_equipment(db)


@router.get("/{loan_id}", response_model=LoanRead, status_code=status.HTTP_200_OK)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    return _service.get_loan(db, loan_id)


@router.post(
    "/{loan_id}/return",
    response_model=LoanRead,
    status_code=status.HTTP_200_OK,
)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    return _service.return_loan(db, loan_id)
