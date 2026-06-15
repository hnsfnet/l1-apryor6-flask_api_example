from flask_sqlalchemy import SQLAlchemy
from app.test.fixtures import app, db  # noqa
from app.widget.model import Widget
from .service import QueryService


def _seed_widgets(db: SQLAlchemy, count: int = 5):
    """Helper to seed widgets for testing."""
    widgets = []
    for i in range(1, count + 1):
        w = Widget(
            widget_id=i,
            name=f"Widget {i}",
            purpose=f"Purpose {i}",
        )
        db.session.add(w)
        widgets.append(w)
    db.session.commit()
    return widgets


class TestQueryServiceGetList:
    """Tests for QueryService.get_list()"""

    def test_get_all_default_pagination(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 5)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
        )
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 20
        assert result["pages"] == 1
        assert len(result["items"]) == 5

    def test_pagination_first_page(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 25)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            page=1,
            per_page=10,
        )
        assert result["total"] == 25
        assert result["page"] == 1
        assert result["per_page"] == 10
        assert result["pages"] == 3
        assert len(result["items"]) == 10

    def test_pagination_second_page(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 25)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            page=2,
            per_page=10,
        )
        assert result["total"] == 25
        assert result["page"] == 2
        assert result["per_page"] == 10
        assert result["pages"] == 3
        assert len(result["items"]) == 10

    def test_pagination_last_page_partial(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 25)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            page=3,
            per_page=10,
        )
        assert result["total"] == 25
        assert result["page"] == 3
        assert result["pages"] == 3
        assert len(result["items"]) == 5

    def test_pagination_beyond_last_page(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 5)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            page=99,
            per_page=10,
        )
        assert result["total"] == 5
        assert result["page"] == 99
        assert result["pages"] == 1
        assert len(result["items"]) == 0

    def test_empty_result(self, db: SQLAlchemy):  # noqa
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
        )
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["per_page"] == 20
        assert result["pages"] == 0
        assert len(result["items"]) == 0

    def test_per_page_clamped_to_max(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            per_page=9999,
        )
        assert result["per_page"] == 100  # MAX_PER_PAGE

    def test_per_page_minimum_one(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            per_page=0,
        )
        assert result["per_page"] == 1

    def test_page_minimum_one(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            page=-5,
        )
        assert result["page"] == 1

    def test_search_by_name(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 5)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            search="Widget 3",
        )
        assert result["total"] == 1
        assert result["items"][0].name == "Widget 3"

    def test_search_by_purpose(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 5)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            search="Purpose 2",
        )
        assert result["total"] == 1
        assert result["items"][0].purpose == "Purpose 2"

    def test_search_case_insensitive(self, db: SQLAlchemy):  # noqa
        w = Widget(widget_id=1, name="Special Item", purpose="Testing")
        db.session.add(w)
        db.session.commit()

        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            search="special",
        )
        assert result["total"] == 1
        assert result["items"][0].name == "Special Item"

    def test_search_partial_match(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 5)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            search="Widget",
        )
        assert result["total"] == 5

    def test_search_no_match(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 5)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            search="nonexistent",
        )
        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_sort_by_id_asc(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            sort_by="id",
            sort_order="asc",
        )
        ids = [item.widget_id for item in result["items"]]
        assert ids == sorted(ids)

    def test_sort_by_id_desc(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            sort_by="id",
            sort_order="desc",
        )
        ids = [item.widget_id for item in result["items"]]
        assert ids == sorted(ids, reverse=True)

    def test_sort_by_name_asc(self, db: SQLAlchemy):  # noqa
        w1 = Widget(widget_id=1, name="Charlie", purpose="p")
        w2 = Widget(widget_id=2, name="Alpha", purpose="p")
        w3 = Widget(widget_id=3, name="Bravo", purpose="p")
        db.session.add_all([w1, w2, w3])
        db.session.commit()

        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            sort_by="name",
            sort_order="asc",
        )
        names = [item.name for item in result["items"]]
        assert names == sorted(names)

    def test_sort_by_name_desc(self, db: SQLAlchemy):  # noqa
        w1 = Widget(widget_id=1, name="Charlie", purpose="p")
        w2 = Widget(widget_id=2, name="Alpha", purpose="p")
        w3 = Widget(widget_id=3, name="Bravo", purpose="p")
        db.session.add_all([w1, w2, w3])
        db.session.commit()

        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            sort_by="name",
            sort_order="desc",
        )
        names = [item.name for item in result["items"]]
        assert names == sorted(names, reverse=True)

    def test_invalid_sort_by_defaults_to_id(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            sort_by="invalid_field",
        )
        ids = [item.widget_id for item in result["items"]]
        assert ids == sorted(ids)

    def test_invalid_sort_order_defaults_to_asc(self, db: SQLAlchemy):  # noqa
        _seed_widgets(db, 3)
        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            sort_order="invalid_order",
        )
        ids = [item.widget_id for item in result["items"]]
        assert ids == sorted(ids)

    def test_search_with_pagination(self, db: SQLAlchemy):  # noqa
        for i in range(1, 11):
            w = Widget(widget_id=i, name=f"Match {i}", purpose="common")
            db.session.add(w)
        db.session.commit()

        result = QueryService.get_list(
            model_class=Widget,
            id_column=Widget.widget_id,
            name_column=Widget.name,
            purpose_column=Widget.purpose,
            search="Match",
            page=1,
            per_page=5,
        )
        assert result["total"] == 10
        assert len(result["items"]) == 5
        assert result["pages"] == 2


class TestQueryServiceParseQueryParams:
    """Tests for QueryService.parse_query_params()"""

    def test_defaults(self):
        result = QueryService.parse_query_params({})
        assert result == {
            "page": 1,
            "per_page": 20,
            "search": None,
            "sort_by": "id",
            "sort_order": "asc",
        }

    def test_valid_params(self):
        result = QueryService.parse_query_params(
            {
                "page": "3",
                "per_page": "50",
                "search": "hello",
                "sort_by": "name",
                "sort_order": "desc",
            }
        )
        assert result == {
            "page": 3,
            "per_page": 50,
            "search": "hello",
            "sort_by": "name",
            "sort_order": "desc",
        }

    def test_invalid_page_type(self):
        result = QueryService.parse_query_params({"page": "abc"})
        assert result["page"] == 1

    def test_invalid_per_page_type(self):
        result = QueryService.parse_query_params({"per_page": "xyz"})
        assert result["per_page"] == 20

    def test_empty_search_becomes_none(self):
        result = QueryService.parse_query_params({"search": "   "})
        assert result["search"] is None

    def test_invalid_sort_by_defaults(self):
        result = QueryService.parse_query_params({"sort_by": "bogus"})
        assert result["sort_by"] == "id"

    def test_invalid_sort_order_defaults(self):
        result = QueryService.parse_query_params({"sort_order": "sideways"})
        assert result["sort_order"] == "asc"
