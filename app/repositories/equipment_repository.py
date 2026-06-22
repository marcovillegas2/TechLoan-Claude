from sqlalchemy.orm import Session
from app.models.equipment import Equipment
from app.schemas.equipment_schema import EquipmentCreate
from datetime import date


class EquipmentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: EquipmentCreate) -> Equipment:
        equipment = Equipment(
            name=data.name,
            brand=data.brand,
            model=data.model,
            serial_number=data.serial_number,
            category=data.category.value,
            status="disponible",
            registration_date=date.today(),
            description=data.description,
        )
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    def get_by_serial_number(self, serial_number: str) -> Equipment | None:
        return (
            self.db.query(Equipment)
            .filter(Equipment.serial_number == serial_number)
            .first()
        )