from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_service = DashboardService()


@router.get("/summary", status_code=status.HTTP_200_OK)
def get_summary(db: Session = Depends(get_db)) -> Dict[str, int]:
    return _service.get_summary(db)


@router.get("/charts", status_code=status.HTTP_200_OK)
def get_charts(db: Session = Depends(get_db)) -> Dict[str, Dict[str, int]]:
    return _service.get_charts(db)


@router.get("/overdue-users", status_code=status.HTTP_200_OK)
def get_overdue_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return _service.get_overdue_users(db)
