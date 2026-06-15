from typing import Any, Dict, Mapping, Optional

from marshmallow import Schema, fields

# Sensible defaults so a list endpoint never dumps a whole table at once.
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


def _to_int(value: Any, default: int) -> int:
    """Best-effort int parse that never raises on junk input."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class QueryService:
    """Shared helpers for list endpoints: pagination, search and sorting.

    Every resource that exposes a "list" route can reuse :meth:`paginate`
    instead of re-implementing the same filtering/ordering logic.
    """

    @staticmethod
    def resolve_page(query_params: Mapping[str, Any]) -> int:
        page = _to_int(query_params.get("page"), DEFAULT_PAGE)
        return page if page >= 1 else DEFAULT_PAGE

    @staticmethod
    def resolve_page_size(query_params: Mapping[str, Any]) -> int:
        page_size = _to_int(query_params.get("page_size"), DEFAULT_PAGE_SIZE)
        if page_size < 1:
            page_size = DEFAULT_PAGE_SIZE
        return min(page_size, MAX_PAGE_SIZE)

    @classmethod
    def paginate(
        cls,
        model: Any,
        query_params: Optional[Mapping[str, Any]] = None,
        *,
        search_fields: Optional[Mapping[str, Any]] = None,
        sort_fields: Optional[Mapping[str, Any]] = None,
        default_sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a page of ``model`` rows plus pagination metadata.

        :param search_fields: mapping of query-param name -> column used for a
            case-insensitive partial match (e.g. ``{"name": Model.name}``).
        :param sort_fields: mapping of public sort key -> column that callers
            are allowed to sort by. Anything else is ignored (never raises).
        :param default_sort: key in ``sort_fields`` used when ``sort_by`` is
            missing or invalid.
        """
        query_params = query_params or {}
        search_fields = search_fields or {}
        sort_fields = sort_fields or {}

        query = model.query

        # --- search: case-insensitive partial match, AND-ed together ---
        for param_name, column in search_fields.items():
            term = query_params.get(param_name)
            if term:
                query = query.filter(column.ilike(f"%{term}%"))

        # --- sort: allow-list the column, fall back instead of crashing ---
        sort_key = query_params.get("sort_by")
        if sort_key not in sort_fields:
            sort_key = default_sort
        if sort_key in sort_fields:
            column = sort_fields[sort_key]
            direction = str(query_params.get("sort_dir", "asc")).lower()
            query = query.order_by(
                column.desc() if direction == "desc" else column.asc()
            )

        # --- pagination ---
        page = cls.resolve_page(query_params)
        page_size = cls.resolve_page_size(query_params)
        total = query.count()
        pages = (total + page_size - 1) // page_size if total else 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
        }


def pagination_schema(item_schema_cls: type, name: Optional[str] = None) -> type:
    """Build a Marshmallow schema that wraps a list of ``item_schema_cls`` rows
    together with pagination metadata, so list responses are self-describing."""
    attrs = {
        "items": fields.Nested(item_schema_cls, many=True),
        "page": fields.Integer(),
        "pageSize": fields.Integer(attribute="page_size"),
        "total": fields.Integer(),
        "pages": fields.Integer(),
    }
    return type(name or f"Paginated{item_schema_cls.__name__}", (Schema,), attrs)


# Reusable Swagger documentation for the shared query parameters.
PAGINATION_DOC = {
    "page": {
        "description": "Page number, 1-based.",
        "type": "integer",
        "default": DEFAULT_PAGE,
    },
    "page_size": {
        "description": f"Items per page (max {MAX_PAGE_SIZE}).",
        "type": "integer",
        "default": DEFAULT_PAGE_SIZE,
    },
    "name": {
        "description": "Case-insensitive partial match on name.",
        "type": "string",
    },
    "purpose": {
        "description": "Case-insensitive partial match on purpose.",
        "type": "string",
    },
    "sort_by": {
        "description": "Field to sort by.",
        "type": "string",
        "enum": ["id", "name"],
        "default": "id",
    },
    "sort_dir": {
        "description": "Sort direction.",
        "type": "string",
        "enum": ["asc", "desc"],
        "default": "asc",
    },
}
