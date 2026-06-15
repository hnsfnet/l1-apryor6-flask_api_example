from flask_sqlalchemy import SQLAlchemy
from typing import List
from app.test.fixtures import app, db  # noqa
from .model import Fizzbaz
from .service import FizzbazService  # noqa
from .interface import FizzbazInterface


def test_get_all(db: SQLAlchemy):  # noqa
    yin: Fizzbaz = Fizzbaz(fizzbaz_id=1, name='Yin', purpose='thing 1')
    yang: Fizzbaz = Fizzbaz(fizzbaz_id=2, name='Yang', purpose='thing 2')
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    results = FizzbazService.get_all()

    assert results["total"] == 2
    assert yin in results["items"] and yang in results["items"]
    assert results["page"] == 1
    assert results["pages"] == 1


def test_get_all_with_pagination(db: SQLAlchemy):  # noqa
    for i in range(1, 11):
        db.session.add(Fizzbaz(fizzbaz_id=i, name=f'Fizzbaz {i}', purpose=f'Purpose {i}'))
    db.session.commit()

    results = FizzbazService.get_all({"page": 1, "per_page": 3})

    assert results["total"] == 10
    assert len(results["items"]) == 3
    assert results["pages"] == 4


def test_get_all_with_search(db: SQLAlchemy):  # noqa
    db.session.add(Fizzbaz(fizzbaz_id=1, name='Alpha Fizzbaz', purpose='Testing'))
    db.session.add(Fizzbaz(fizzbaz_id=2, name='Beta Fizzbaz', purpose='Production'))
    db.session.commit()

    results = FizzbazService.get_all({"search": "Alpha"})

    assert results["total"] == 1
    assert results["items"][0].name == "Alpha Fizzbaz"


def test_get_all_with_sorting(db: SQLAlchemy):  # noqa
    db.session.add(Fizzbaz(fizzbaz_id=1, name="Charlie", purpose="p"))
    db.session.add(Fizzbaz(fizzbaz_id=2, name="Alpha", purpose="p"))
    db.session.add(Fizzbaz(fizzbaz_id=3, name="Bravo", purpose="p"))
    db.session.commit()

    results = FizzbazService.get_all({"sort_by": "name", "sort_order": "asc"})

    names = [item.name for item in results["items"]]
    assert names == ["Alpha", "Bravo", "Charlie"]


def test_get_all_empty(db: SQLAlchemy):  # noqa
    results = FizzbazService.get_all()
    assert results["total"] == 0
    assert results["items"] == []
    assert results["pages"] == 0


def test_update(db: SQLAlchemy):  # noqa
    yin: Fizzbaz = Fizzbaz(fizzbaz_id=1, name='Yin', purpose='thing 1')

    db.session.add(yin)
    db.session.commit()
    updates: FizzbazInterface = dict(name='New Fizzbaz name')

    FizzbazService.update(yin, updates)

    result: Fizzbaz = Fizzbaz.query.get(yin.fizzbaz_id)
    assert result.name == 'New Fizzbaz name'


def test_delete_by_id(db: SQLAlchemy):  # noqa
    yin: Fizzbaz = Fizzbaz(fizzbaz_id=1, name='Yin', purpose='thing 1')
    yang: Fizzbaz = Fizzbaz(fizzbaz_id=2, name='Yang', purpose='thing 2')
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    FizzbazService.delete_by_id(1)
    db.session.commit()

    results: List[Fizzbaz] = Fizzbaz.query.all()

    assert len(results) == 1
    assert yin not in results and yang in results


def test_create(db: SQLAlchemy):  # noqa

    yin: FizzbazInterface = dict(name='Fancy new fizzbaz', purpose='Fancy new purpose')
    FizzbazService.create(yin)
    results: List[Fizzbaz] = Fizzbaz.query.all()

    assert len(results) == 1

    for k in yin.keys():
        assert getattr(results[0], k) == yin[k]
