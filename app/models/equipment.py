from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.sql import func
from app.database.connection import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="disponible")
    registration_date = Column(Date, nullable=False, server_default=func.current_date())
    description = Column(Text, nullable=True)