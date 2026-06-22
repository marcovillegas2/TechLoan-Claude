from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from enum import Enum


class EquipmentCategory(str, Enum):
    laptop = "laptop"
    desktop = "desktop"
    tablet = "tablet"
    proyector = "proyector"
    camara = "camara"
    otro = "otro"


class EquipmentStatus(str, Enum):
    disponible = "disponible"
    prestado = "prestado"
    mantenimiento = "en mantenimiento"


class EquipmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Laptop HP ProBook"])
    brand: str = Field(..., min_length=2, max_length=100, examples=["HP"])
    model: str = Field(..., min_length=1, max_length=100, examples=["ProBook 450 G9"])
    serial_number: str = Field(..., min_length=3, max_length=100, examples=["SN-2024-00123"])
    category: EquipmentCategory
    description: Optional[str] = Field(None, max_length=500)


class EquipmentResponse(BaseModel):
    id: int
    name: str
    brand: str
    model: str
    serial_number: str
    category: str
    status: str
    registration_date: date
    description: Optional[str]

    model_config = {"from_attributes": True}