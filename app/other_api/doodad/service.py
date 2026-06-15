from app import db
from typing import List
from app.shared.errors import NotFoundError, validate_nonempty, validate_required
from .model import Doodad
from .interface import DoodadInterface


class DoodadService:
    @staticmethod
    def get_all() -> List[Doodad]:
        return Doodad.query.all()

    @staticmethod
    def get_by_id(doodad_id: int) -> Doodad:
        doodad = Doodad.query.get(doodad_id)
        if doodad is None:
            raise NotFoundError("Doodad", doodad_id)
        return doodad

    @staticmethod
    def update(doodad: Doodad, Doodad_change_updates: DoodadInterface) -> Doodad:
        validate_nonempty(Doodad_change_updates, ("name", "purpose"))
        doodad.update(Doodad_change_updates)
        db.session.commit()
        return doodad

    @staticmethod
    def delete_by_id(doodad_id: int) -> int:
        doodad = Doodad.query.filter(Doodad.doodad_id == doodad_id).first()
        if not doodad:
            raise NotFoundError("Doodad", doodad_id)
        db.session.delete(doodad)
        db.session.commit()
        return doodad_id

    @staticmethod
    def create(new_attrs: DoodadInterface) -> Doodad:
        validate_required(new_attrs, ("name", "purpose"))
        new_doodad = Doodad(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_doodad)
        db.session.commit()

        return new_doodad
