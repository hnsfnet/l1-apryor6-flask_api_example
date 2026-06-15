from app import db
from typing import Any, Dict, List
from .model import Fizzbar
from .interface import FizzbarInterface
from app.shared.query.service import QueryService


class FizzbarService:
    @staticmethod
    def get_all(query_params: Dict[str, Any] = None) -> Dict[str, Any]:
        if query_params is None:
            query_params = {}
        return QueryService.get_list(
            model_class=Fizzbar,
            id_column=Fizzbar.fizzbar_id,
            name_column=Fizzbar.name,
            purpose_column=Fizzbar.purpose,
            **query_params,
        )

    @staticmethod
    def get_by_id(fizzbar_id: int) -> Fizzbar:
        return Fizzbar.query.get(fizzbar_id)

    @staticmethod
    def update(fizzbar: Fizzbar, Fizzbar_change_updates: FizzbarInterface) -> Fizzbar:
        fizzbar.update(Fizzbar_change_updates)
        db.session.commit()
        return fizzbar

    @staticmethod
    def delete_by_id(fizzbar_id: int) -> List[int]:
        fizzbar = Fizzbar.query.filter(Fizzbar.fizzbar_id == fizzbar_id).first()
        if not fizzbar:
            return []
        db.session.delete(fizzbar)
        db.session.commit()
        return [fizzbar_id]

    @staticmethod
    def create(new_attrs: FizzbarInterface) -> Fizzbar:
        new_fizzbar = Fizzbar(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_fizzbar)
        db.session.commit()

        return new_fizzbar
