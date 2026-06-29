from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.borrower_schema import BorrowerCreate, BorrowerRead, BorrowerUpdate
from app.services.borrower_service import BorrowerService

router = APIRouter(prefix="/borrowers", tags=["Borrowers"])

_service = BorrowerService()


@router.post("/", response_model=BorrowerRead, status_code=status.HTTP_201_CREATED)
def create_borrower(data: BorrowerCreate, db: Session = Depends(get_db)):
    return _service.create_borrower(db, data)


@router.get("/", response_model=List[BorrowerRead], status_code=status.HTTP_200_OK)
def list_borrowers(db: Session = Depends(get_db)):
    return _service.list_borrowers(db)


@router.get("/{borrower_id}", response_model=BorrowerRead, status_code=status.HTTP_200_OK)
def get_borrower(borrower_id: int, db: Session = Depends(get_db)):
    return _service.get_borrower(db, borrower_id)


@router.put("/{borrower_id}", response_model=BorrowerRead, status_code=status.HTTP_200_OK)
def update_borrower(
    borrower_id: int,
    data: BorrowerUpdate,
    db: Session = Depends(get_db),
):
    return _service.update_borrower(db, borrower_id, data)
