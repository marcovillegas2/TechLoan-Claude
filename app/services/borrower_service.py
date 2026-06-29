from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.borrower_repository import BorrowerRepository
from app.schemas.borrower_schema import BorrowerCreate, BorrowerUpdate

_repository = BorrowerRepository()


class BorrowerService:

    def create_borrower(self, db: Session, data: BorrowerCreate):
        if _repository.get_by_dni(db, data.dni):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El DNI '{data.dni}' ya está registrado.",
            )

        borrower_data = data.model_dump()
        borrower_data["created_at"] = datetime.utcnow()

        return _repository.create(db, borrower_data)

    def get_borrower(self, db: Session, borrower_id: int):
        borrower = _repository.get_by_id(db, borrower_id)
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitante con id {borrower_id} no encontrado.",
            )
        return borrower

    def list_borrowers(self, db: Session) -> List:
        return _repository.get_all(db)

    def update_borrower(self, db: Session, borrower_id: int, data: BorrowerUpdate):
        borrower = _repository.get_by_id(db, borrower_id)
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitante con id {borrower_id} no encontrado.",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "dni" in update_data and update_data["dni"] != borrower.dni:
            if _repository.get_by_dni(db, update_data["dni"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El DNI '{update_data['dni']}' ya está registrado.",
                )

        return _repository.update(db, borrower, update_data)
