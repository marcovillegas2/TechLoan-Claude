from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.loan import Loan


class LoanRepository:

    def create(self, db: Session, data: dict) -> Loan:
        loan = Loan(**data)
        db.add(loan)
        db.commit()
        db.refresh(loan)
        return loan

    def get_by_id(self, db: Session, loan_id: int) -> Optional[Loan]:
        return db.query(Loan).filter(Loan.id == loan_id).first()

    def get_all(self, db: Session) -> List[Loan]:
        return db.query(Loan).all()

    def update(self, db: Session, loan: Loan, data: dict) -> Loan:
        for field, value in data.items():
            setattr(loan, field, value)
        loan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(loan)
        return loan

    def get_equipment_by_id(self, db: Session, equipment_id: int) -> Optional[Equipment]:
        return db.query(Equipment).filter(Equipment.id == equipment_id).first()

    def update_equipment_status(
        self, db: Session, equipment_id: int, new_status: str
    ) -> None:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if equipment:
            equipment.status = new_status
            equipment.updated_at = datetime.utcnow()
            db.commit()

    def get_available_equipment(self, db: Session) -> List[Equipment]:
        return (
            db.query(Equipment).filter(Equipment.status == "DISPONIBLE").all()
        )
