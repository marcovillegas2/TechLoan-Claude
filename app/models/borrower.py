from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dni = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    department = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    loans = relationship("Loan", back_populates="borrower")
