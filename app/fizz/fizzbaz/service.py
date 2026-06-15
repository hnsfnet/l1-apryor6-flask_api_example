from app import db
from typing import List
from app.shared.errors import NotFoundError, validate_nonempty, validate_required
from .model import Fizzbaz
from .interface import FizzbazInterface


class FizzbazService():
    @staticmethod
    def get_all() -> List[Fizzbaz]:
        return Fizzbaz.query.all()

    @staticmethod
    def get_by_id(fizzbaz_id: int) -> Fizzbaz:
        fizzbaz = Fizzbaz.query.get(fizzbaz_id)
        if fizzbaz is None:
            raise NotFoundError("Fizzbaz", fizzbaz_id)
        return fizzbaz

    @staticmethod
    def update(fizzbaz: Fizzbaz, Fizzbaz_change_updates: FizzbazInterface) -> Fizzbaz:
        validate_nonempty(Fizzbaz_change_updates, ("name", "purpose"))
        fizzbaz.update(Fizzbaz_change_updates)
        db.session.commit()
        return fizzbaz

    @staticmethod
    def delete_by_id(fizzbaz_id: int) -> int:
        fizzbaz = Fizzbaz.query.filter(Fizzbaz.fizzbaz_id == fizzbaz_id).first()
        if not fizzbaz:
            raise NotFoundError("Fizzbaz", fizzbaz_id)
        db.session.delete(fizzbaz)
        db.session.commit()
        return fizzbaz_id

    @staticmethod
    def create(new_attrs: FizzbazInterface) -> Fizzbaz:
        validate_required(new_attrs, ("name", "purpose"))
        new_fizzbaz = Fizzbaz(
            name=new_attrs['name'],
            purpose=new_attrs['purpose']
        )

        db.session.add(new_fizzbaz)
        db.session.commit()

        return new_fizzbaz
