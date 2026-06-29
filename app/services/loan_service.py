from datetime import date, datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.borrower_repository import BorrowerRepository
from app.repositories.loan_repository import LoanRepository
from app.schemas.loan_schema import LoanCreate

_loan_repo = LoanRepository()
_borrower_repo = BorrowerRepository()


class LoanService:

    def create_loan(self, db: Session, data: LoanCreate):
        # 1. Verificar que el equipo existe
        equipment = _loan_repo.get_equipment_by_id(db, data.equipment_id)
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con id {data.equipment_id} no encontrado.",
            )

        # 2. Verificar que el equipo está disponible
        if equipment.status != "DISPONIBLE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El equipo no está disponible para préstamo.",
            )

        # 3. Verificar que el solicitante existe
        borrower = _borrower_repo.get_by_id(db, data.borrower_id)
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitante con id {data.borrower_id} no encontrado.",
            )

        # 4. Validar que la fecha límite es posterior a la fecha de préstamo
        if data.due_date <= data.loan_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La fecha límite de devolución debe ser posterior a la fecha de préstamo.",
            )

        # 5. Crear el préstamo (estado siempre ACTIVO, return_date siempre nulo)
        loan_data = data.model_dump()
        loan_data["status"] = "ACTIVO"
        loan_data["return_date"] = None
        loan_data["created_at"] = datetime.utcnow()

        loan = _loan_repo.create(db, loan_data)

        # 6. Marcar el equipo como PRESTADO
        _loan_repo.update_equipment_status(db, data.equipment_id, "PRESTADO")

        return loan

    def get_loan(self, db: Session, loan_id: int):
        loan = _loan_repo.get_by_id(db, loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Préstamo con id {loan_id} no encontrado.",
            )
        return loan

    def list_loans(self, db: Session) -> List:
        return _loan_repo.get_all(db)

    def return_loan(self, db: Session, loan_id: int):
        loan = _loan_repo.get_by_id(db, loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Préstamo con id {loan_id} no encontrado.",
            )

        if loan.status != "ACTIVO":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Solo se pueden devolver préstamos en estado ACTIVO.",
            )

        # Guardar el equipment_id antes de la actualización
        equipment_id = loan.equipment_id

        loan = _loan_repo.update(
            db,
            loan,
            {"status": "DEVUELTO", "return_date": date.today()},
        )

        # Marcar el equipo como DISPONIBLE
        _loan_repo.update_equipment_status(db, equipment_id, "DISPONIBLE")

        return loan

    def get_available_equipment(self, db: Session) -> List:
        return _loan_repo.get_available_equipment(db)
