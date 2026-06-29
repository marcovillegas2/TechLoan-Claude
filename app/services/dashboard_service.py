"""
Dashboard Service — Sprint 3 (HU07, HU08).
Agrega métricas del sistema reutilizando los repositories existentes.
"""
from datetime import date
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.repositories.borrower_repository import BorrowerRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.loan_repository import LoanRepository

_equipment_repo = EquipmentRepository()
_borrower_repo = BorrowerRepository()
_loan_repo = LoanRepository()


class DashboardService:

    def get_summary(self, db: Session) -> Dict[str, int]:
        """Resumen general del sistema (HU07)."""
        equipments = _equipment_repo.get_all(db)
        loans = _loan_repo.get_all(db)
        today = date.today()

        overdue_loans = [
            loan for loan in loans
            if loan.due_date < today and loan.return_date is None
        ]

        return {
            "total_equipment": len(equipments),
            "available_equipment": sum(
                1 for e in equipments if e.status == "DISPONIBLE"
            ),
            "loaned_equipment": sum(
                1 for e in equipments if e.status == "PRESTADO"
            ),
            "overdue_loans": len(overdue_loans),
            "overdue_borrowers": len({loan.borrower_id for loan in overdue_loans}),
        }

    def get_charts(self, db: Session) -> Dict[str, Dict[str, int]]:
        """Distribución de préstamos y equipos por estado (HU07)."""
        equipments = _equipment_repo.get_all(db)
        loans = _loan_repo.get_all(db)

        return {
            "loans_by_status": {
                "ACTIVO": sum(1 for loan in loans if loan.status == "ACTIVO"),
                "DEVUELTO": sum(1 for loan in loans if loan.status == "DEVUELTO"),
                "VENCIDO": sum(1 for loan in loans if loan.status == "VENCIDO"),
            },
            "equipment_by_status": {
                "DISPONIBLE": sum(1 for e in equipments if e.status == "DISPONIBLE"),
                "PRESTADO": sum(1 for e in equipments if e.status == "PRESTADO"),
            },
        }

    def get_overdue_users(self, db: Session) -> List[Dict[str, Any]]:
        """Usuarios con devoluciones vencidas (HU08).

        Un préstamo es vencido cuando su due_date expiró y return_date es nulo,
        independientemente del valor almacenado en el campo status.
        """
        loans = _loan_repo.get_all(db)
        today = date.today()
        result = []

        for loan in loans:
            if loan.due_date < today and loan.return_date is None:
                result.append({
                    "loan_id": loan.id,
                    "borrower_full_name": loan.borrower.full_name,
                    "borrower_dni": loan.borrower.dni,
                    "equipment_name": loan.equipment.name,
                    "due_date": loan.due_date.isoformat(),
                    "days_overdue": (today - loan.due_date).days,
                    "loan_status": loan.status,
                })

        return result
