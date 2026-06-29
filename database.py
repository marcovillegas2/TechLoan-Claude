import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_DIR = "database"
DATABASE_FILE = "techloan.db"
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/{DATABASE_FILE}"

os.makedirs(DATABASE_DIR, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Importar modelos
from app.models import equipment, borrower, loan

# Crear las tablas
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()