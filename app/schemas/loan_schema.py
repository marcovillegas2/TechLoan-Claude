from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LoanStatus(str, Enum):
    ACTIVO = "ACTIVO"
    DEVUELTO = "DEVUELTO"
    VENCIDO = "VENCIDO"


class LoanCreate(BaseModel):
    equipment_id: int
    borrower_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    status: LoanStatus


class LoanUpdate(BaseModel):
    equipment_id: Optional[int] = None
    borrower_id: Optional[int] = None
    loan_date: Optional[date] = None
    due_date: Optional[date] = None
    return_date: Optional[date] = None
    status: Optional[LoanStatus] = None


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: int
    borrower_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    status: LoanStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
