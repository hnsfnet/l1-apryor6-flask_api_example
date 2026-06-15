from app import db
from typing import List
from app.shared.errors import NotFoundError, validate_nonempty, validate_required
from .model import Fizzbar
from .interface import FizzbarInterface


class FizzbarService:
    @staticmethod
    def get_all() -> List[Fizzbar]:
        return Fizzbar.query.all()

    @staticmethod
    def get_by_id(fizzbar_id: int) -> Fizzbar:
        fizzbar = Fizzbar.query.get(fizzbar_id)
        if fizzbar is None:
            raise NotFoundError("Fizzbar", fizzbar_id)
        return fizzbar

    @staticmethod
    def update(fizzbar: Fizzbar, Fizzbar_change_updates: FizzbarInterface) -> Fizzbar:
        validate_nonempty(Fizzbar_change_updates, ("name", "purpose"))
        fizzbar.update(Fizzbar_change_updates)
        db.session.commit()
        return fizzbar

    @staticmethod
    def delete_by_id(fizzbar_id: int) -> int:
        fizzbar = Fizzbar.query.filter(Fizzbar.fizzbar_id == fizzbar_id).first()
        if not fizzbar:
            raise NotFoundError("Fizzbar", fizzbar_id)
        db.session.delete(fizzbar)
        db.session.commit()
        return fizzbar_id

    @staticmethod
    def create(new_attrs: FizzbarInterface) -> Fizzbar:
        validate_required(new_attrs, ("name", "purpose"))
        new_fizzbar = Fizzbar(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_fizzbar)
        db.session.commit()

        return new_fizzbar
