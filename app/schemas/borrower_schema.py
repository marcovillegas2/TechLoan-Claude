from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BorrowerCreate(BaseModel):
    dni: str
    full_name: str
    email: str
    phone: str
    department: str


class BorrowerUpdate(BaseModel):
    dni: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None


class BorrowerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dni: str
    full_name: str
    email: str
    phone: str
    department: str
    created_at: datetime
