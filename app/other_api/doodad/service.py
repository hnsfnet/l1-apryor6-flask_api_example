from app import db
from typing import Any, Dict, List, Sequence
from app.shared.bulk import BulkService
from .model import Doodad
from .interface import DoodadInterface

DOODAD_FIELDS = ("name", "purpose")


class DoodadService:
    @staticmethod
    def get_all() -> List[Doodad]:
        return Doodad.query.all()

    @staticmethod
    def get_by_id(doodad_id: int) -> Doodad:
        return Doodad.query.get(doodad_id)

    @staticmethod
    def update(doodad: Doodad, Doodad_change_updates: DoodadInterface) -> Doodad:
        doodad.update(Doodad_change_updates)
        db.session.commit()
        return doodad

    @staticmethod
    def delete_by_id(doodad_id: int) -> List[int]:
        doodad = Doodad.query.filter(Doodad.doodad_id == doodad_id).first()
        if not doodad:
            return []
        db.session.delete(doodad)
        db.session.commit()
        return [doodad_id]

    @staticmethod
    def create(new_attrs: DoodadInterface) -> Doodad:
        new_doodad = Doodad(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_doodad)
        db.session.commit()

        return new_doodad

    @staticmethod
    def create_bulk(items: Sequence[DoodadInterface]) -> Dict[str, Any]:
        """Create many Doodads, reporting per-item success/failure."""
        return BulkService.bulk_create(Doodad, items, DOODAD_FIELDS)

    @staticmethod
    def delete_bulk(doodad_ids: Sequence[int]) -> Dict[str, Any]:
        """Delete many Doodads by id, reporting which ids were not found."""
        return BulkService.bulk_delete(Doodad, Doodad.doodad_id, doodad_ids)
