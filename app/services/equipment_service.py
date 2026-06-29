from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipment_repository import EquipmentRepository
from app.schemas.equipment_schema import EquipmentCreate, EquipmentUpdate

_repository = EquipmentRepository()


class EquipmentService:

    def create_equipment(self, db: Session, data: EquipmentCreate):
        if _repository.get_by_code(db, data.code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El código de equipo '{data.code}' ya está registrado.",
            )

        equipment_data = data.model_dump(mode="json")
        equipment_data["created_at"] = datetime.utcnow()

        return _repository.create(db, equipment_data)

    def get_equipment(self, db: Session, equipment_id: int):
        equipment = _repository.get_by_id(db, equipment_id)
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con id {equipment_id} no encontrado.",
            )
        return equipment

    def list_equipment(self, db: Session) -> List:
        return _repository.get_all(db)

    def update_equipment(self, db: Session, equipment_id: int, data: EquipmentUpdate):
        equipment = _repository.get_by_id(db, equipment_id)
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con id {equipment_id} no encontrado.",
            )

        update_data = data.model_dump(exclude_unset=True, mode="json")

        if "code" in update_data and update_data["code"] != equipment.code:
            if _repository.get_by_code(db, update_data["code"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El código de equipo '{update_data['code']}' ya está registrado.",
                )

        return _repository.update(db, equipment, update_data)

    def delete_equipment(self, db: Session, equipment_id: int) -> dict:
        equipment = _repository.get_by_id(db, equipment_id)
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con id {equipment_id} no encontrado.",
            )

        if _repository.has_active_loans(db, equipment_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar el equipo porque tiene préstamos activos.",
            )

        _repository.delete(db, equipment)
        return {"message": "Equipo eliminado correctamente."}
