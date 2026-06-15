from app import db
from typing import List
from app.shared.errors import NotFoundError, validate_nonempty, validate_required
from .model import Whatsit
from .interface import WhatsitInterface


class WhatsitService:
    @staticmethod
    def get_all() -> List[Whatsit]:
        return Whatsit.query.all()

    @staticmethod
    def get_by_id(whatsit_id: int) -> Whatsit:
        whatsit = Whatsit.query.get(whatsit_id)
        if whatsit is None:
            raise NotFoundError("Whatsit", whatsit_id)
        return whatsit

    @staticmethod
    def update(whatsit: Whatsit, Whatsit_change_updates: WhatsitInterface) -> Whatsit:
        validate_nonempty(Whatsit_change_updates, ("name", "purpose"))
        whatsit.update(Whatsit_change_updates)
        db.session.commit()
        return whatsit

    @staticmethod
    def delete_by_id(whatsit_id: int) -> int:
        whatsit = Whatsit.query.filter(Whatsit.whatsit_id == whatsit_id).first()
        if not whatsit:
            raise NotFoundError("Whatsit", whatsit_id)
        db.session.delete(whatsit)
        db.session.commit()
        return whatsit_id

    @staticmethod
    def create(new_attrs: WhatsitInterface) -> Whatsit:
        validate_required(new_attrs, ("name", "purpose"))
        new_whatsit = Whatsit(name=new_attrs["name"], purpose=new_attrs["purpose"])

        db.session.add(new_whatsit)
        db.session.commit()

        return new_whatsit
