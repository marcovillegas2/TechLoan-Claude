from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.loan import Loan


class EquipmentRepository:

    def create(self, db: Session, data: dict) -> Equipment:
        equipment = Equipment(**data)
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        return equipment

    def get_by_id(self, db: Session, equipment_id: int) -> Optional[Equipment]:
        return db.query(Equipment).filter(Equipment.id == equipment_id).first()

    def get_by_code(self, db: Session, code: str) -> Optional[Equipment]:
        return db.query(Equipment).filter(Equipment.code == code).first()

    def get_all(self, db: Session) -> List[Equipment]:
        return db.query(Equipment).all()

    def update(self, db: Session, equipment: Equipment, data: dict) -> Equipment:
        for field, value in data.items():
            setattr(equipment, field, value)
        equipment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(equipment)
        return equipment

    def delete(self, db: Session, equipment: Equipment) -> None:
        db.delete(equipment)
        db.commit()

    def has_active_loans(self, db: Session, equipment_id: int) -> bool:
        return (
            db.query(Loan)
            .filter(
                Loan.equipment_id == equipment_id,
                Loan.status == "ACTIVO",
                Loan.return_date.is_(None),
            )
            .first()
            is not None
        )
