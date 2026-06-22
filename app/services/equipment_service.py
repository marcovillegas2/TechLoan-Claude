from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.equipment_repository import EquipmentRepository
from app.schemas.equipment_schema import EquipmentCreate, EquipmentResponse


class EquipmentService:

    def __init__(self, db: Session):
        self.repository = EquipmentRepository(db)

    def register_equipment(self, data: EquipmentCreate) -> EquipmentResponse:
        self._validate_serial_number_unique(data.serial_number)
        self._validate_serial_number_format(data.serial_number)

        equipment = self.repository.create(data)
        return EquipmentResponse.model_validate(equipment)

    # ── Private validations ──────────────────────────────────────────────────

    def _validate_serial_number_unique(self, serial_number: str) -> None:
        existing = self.repository.get_by_serial_number(serial_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un equipo con el número de serie '{serial_number}'.",
            )

    def _validate_serial_number_format(self, serial_number: str) -> None:
        cleaned = serial_number.strip()
        if len(cleaned) < 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El número de serie debe tener al menos 3 caracteres.",
            )
        if " " in cleaned:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El número de serie no puede contener espacios.",
            )