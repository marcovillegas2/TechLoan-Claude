from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("borrowers.id"), nullable=False)
    loan_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    equipment = relationship("Equipment", back_populates="loans")
    borrower = relationship("Borrower", back_populates="loans")
