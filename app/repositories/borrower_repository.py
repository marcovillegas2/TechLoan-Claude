from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.borrower import Borrower


class BorrowerRepository:

    def create(self, db: Session, data: dict) -> Borrower:
        borrower = Borrower(**data)
        db.add(borrower)
        db.commit()
        db.refresh(borrower)
        return borrower

    def get_by_id(self, db: Session, borrower_id: int) -> Optional[Borrower]:
        return db.query(Borrower).filter(Borrower.id == borrower_id).first()

    def get_by_dni(self, db: Session, dni: str) -> Optional[Borrower]:
        return db.query(Borrower).filter(Borrower.dni == dni).first()

    def get_all(self, db: Session) -> List[Borrower]:
        return db.query(Borrower).all()

    def update(self, db: Session, borrower: Borrower, data: dict) -> Borrower:
        for field, value in data.items():
            setattr(borrower, field, value)
        db.commit()
        db.refresh(borrower)
        return borrower
