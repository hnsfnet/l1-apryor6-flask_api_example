from flask_sqlalchemy import SQLAlchemy
from typing import List
from app.test.fixtures import app, db  # noqa
from .model import Doodad
from .service import DoodadService  # noqa
from .interface import DoodadInterface


def test_get_all(db: SQLAlchemy):  # noqa
    yin: Doodad = Doodad(doodad_id=1, name="Yin", purpose="thing 1")
    yang: Doodad = Doodad(doodad_id=2, name="Yang", purpose="thing 2")
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    results: List[Doodad] = DoodadService.get_all()

    assert len(results) == 2
    assert yin in results and yang in results


def test_update(db: SQLAlchemy):  # noqa
    yin: Doodad = Doodad(doodad_id=1, name="Yin", purpose="thing 1")

    db.session.add(yin)
    db.session.commit()
    updates: DoodadInterface = dict(name="New Doodad name")

    DoodadService.update(yin, updates)

    result: Doodad = Doodad.query.get(yin.doodad_id)
    assert result.name == "New Doodad name"


def test_delete_by_id(db: SQLAlchemy):  # noqa
    yin: Doodad = Doodad(doodad_id=1, name="Yin", purpose="thing 1")
    yang: Doodad = Doodad(doodad_id=2, name="Yang", purpose="thing 2")
    db.session.add(yin)
    db.session.add(yang)
    db.session.commit()

    DoodadService.delete_by_id(1)
    db.session.commit()

    results: List[Doodad] = Doodad.query.all()

    assert len(results) == 1
    assert yin not in results and yang in results


def test_create(db: SQLAlchemy):  # noqa

    yin: DoodadInterface = dict(name="Fancy new doodad", purpose="Fancy new purpose")
    DoodadService.create(yin)
    results: List[Doodad] = Doodad.query.all()

    assert len(results) == 1

    for k in yin.keys():
        assert getattr(results[0], k) == yin[k]


def test_create_bulk(db: SQLAlchemy):  # noqa
    items = [
        dict(name="Bulk 1", purpose="p1"),
        dict(name="Bulk 2", purpose="p2"),
        dict(name="No purpose"),  # invalid -> should be reported, not written
    ]

    result = DoodadService.create_bulk(items)

    assert result["success_count"] == 2
    assert result["failure_count"] == 1
    assert result["failed"][0]["index"] == 2
    assert "purpose" in result["failed"][0]["error"]

    rows: List[Doodad] = Doodad.query.all()
    assert len(rows) == 2
    assert {r.name for r in rows} == {"Bulk 1", "Bulk 2"}


def test_delete_bulk(db: SQLAlchemy):  # noqa
    db.session.add(Doodad(doodad_id=1, name="Yin", purpose="p"))
    db.session.add(Doodad(doodad_id=2, name="Yang", purpose="p"))
    db.session.commit()

    result = DoodadService.delete_bulk([1, 2, 99, 1])

    assert result["deleted"] == [1, 2]
    assert result["not_found"] == [99, 1]
    assert result["success_count"] == 2
    assert result["failure_count"] == 2
    assert Doodad.query.all() == []
