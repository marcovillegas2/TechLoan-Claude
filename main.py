from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import Base, engine
from app.controllers.equipment_controller import router as equipment_router

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TechLoan API",
    description="Sistema de Préstamo de Equipos Tecnológicos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(equipment_router, prefix="/api/v1")

app.mount("/", StaticFiles(directory="frontend/html", html=True), name="frontend")