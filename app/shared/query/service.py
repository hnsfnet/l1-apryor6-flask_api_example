from typing import Dict, List, Optional, Type
from sqlalchemy import text
from app import db


class QueryService:
    """Shared service for common query operations across modules."""

    @staticmethod
    def get_count(model_cls: Type[db.Model]) -> int:
        """Return the total number of records for a given model."""
        try:
            return model_cls.query.count()
        except Exception:
            return 0

    @staticmethod
    def get_latest(model_cls: Type[db.Model], id_column: str) -> Optional[Dict]:
        """Return the latest record (by primary key) for a given model as a dict.

        Returns None if no records exist.
        """
        try:
            pk = getattr(model_cls, id_column)
            record = model_cls.query.order_by(pk.desc()).first()
            if record is None:
                return None
            return {
                "id": getattr(record, id_column),
                "name": record.name,
                "purpose": record.purpose,
            }
        except Exception:
            return None

    @staticmethod
    def get_resource_summary(
        resources: List[Dict[str, str]]
    ) -> Dict[str, Dict]:
        """Build a summary dict for a list of resource descriptors.

        Each descriptor is a dict with keys:
            name   - the resource label (e.g. "widget")
            model  - the SQLAlchemy model class
            id_col - the primary key column attribute name
        """
        summary = {}
        for res in resources:
            name = res["name"]
            model_cls = res["model"]
            id_col = res["id_col"]
            summary[name] = {
                "count": QueryService.get_count(model_cls),
                "latest": QueryService.get_latest(model_cls, id_col),
            }
        return summary

    @staticmethod
    def check_db_connectivity() -> bool:
        """Return True if the database session can execute a simple query."""
        try:
            db.session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
