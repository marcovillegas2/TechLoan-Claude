from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EquipmentStatus(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    PRESTADO = "PRESTADO"


class EquipmentCreate(BaseModel):
    code: str
    name: str
    category: str
    description: Optional[str] = None
    status: EquipmentStatus


class EquipmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[EquipmentStatus] = None


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    description: Optional[str] = None
    status: EquipmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
