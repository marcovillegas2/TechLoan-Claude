from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.equipment_schema import EquipmentCreate, EquipmentResponse
from app.services.equipment_service import EquipmentService

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post(
    "/",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo equipo",
    description="Registra un equipo tecnológico en el inventario. "
                "El número de serie debe ser único.",
)
def register_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
):
    service = EquipmentService(db)
    return service.register_equipment(payload)