from app import db
from typing import List, Tuple, Dict
from .model import Doodad
from .interface import DoodadInterface
from app.shared.batch import batch_create, batch_delete


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
    def create_many(items: List[dict]) -> Tuple[List[Doodad], List[Dict]]:
        """
        Batch create doodads.

        Args:
            items: List of dicts with 'name' and optional 'purpose'.

        Returns:
            Tuple of (successful_doodads, failed_items).
        """
        return batch_create(Doodad, items)

    @staticmethod
    def delete_many(ids: List[int]) -> Tuple[List[int], List[Dict]]:
        """
        Batch delete doodads by ID.

        Args:
            ids: List of doodad IDs to delete.

        Returns:
            Tuple of (successful_ids, failed_items).
        """
        return batch_delete(Doodad, ids, Doodad.doodad_id)
