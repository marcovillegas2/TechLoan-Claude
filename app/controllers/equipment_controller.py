from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.equipment_schema import EquipmentCreate, EquipmentRead, EquipmentUpdate
from app.services.equipment_service import EquipmentService

router = APIRouter(prefix="/equipment", tags=["Equipment"])

_service = EquipmentService()


@router.post("/", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(data: EquipmentCreate, db: Session = Depends(get_db)):
    return _service.create_equipment(db, data)


@router.get("/", response_model=List[EquipmentRead], status_code=status.HTTP_200_OK)
def list_equipment(db: Session = Depends(get_db)):
    return _service.list_equipment(db)


@router.get("/{equipment_id}", response_model=EquipmentRead, status_code=status.HTTP_200_OK)
def get_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return _service.get_equipment(db, equipment_id)


@router.put("/{equipment_id}", response_model=EquipmentRead, status_code=status.HTTP_200_OK)
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
):
    return _service.update_equipment(db, equipment_id, data)


@router.delete("/{equipment_id}", status_code=status.HTTP_200_OK)
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return _service.delete_equipment(db, equipment_id)
