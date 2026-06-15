from typing import Any, Dict, List, Optional, Type
from math import ceil

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100

ALLOWED_SORT_BY = ("name", "id")
ALLOWED_SORT_ORDER = ("asc", "desc")


class QueryService:
    """Shared query service providing pagination, filtering, and sorting
    for any SQLAlchemy model that has name, purpose, and a primary key column."""

    @staticmethod
    def get_list(
        model_class: Type,
        id_column: Any,
        name_column: Any,
        purpose_column: Any,
        page: int = DEFAULT_PAGE,
        per_page: int = DEFAULT_PER_PAGE,
        search: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> Dict[str, Any]:
        """Execute a paginated, filtered, and sorted query.

        Args:
            model_class: The SQLAlchemy model class to query.
            id_column: The primary key column attribute (e.g. Widget.widget_id).
            name_column: The name column attribute (e.g. Widget.name).
            purpose_column: The purpose column attribute (e.g. Widget.purpose).
            page: Page number (1-based). Defaults to 1.
            per_page: Number of items per page. Defaults to 20, max 100.
            search: Optional search string for fuzzy matching on name and purpose.
            sort_by: Field to sort by. One of 'name' or 'id'. Defaults to 'id'.
            sort_order: Sort direction. One of 'asc' or 'desc'. Defaults to 'asc'.

        Returns:
            A dict with keys: items, total, page, per_page, pages.
        """
        # Sanitize page and per_page
        page = max(1, page)
        per_page = min(max(1, per_page), MAX_PER_PAGE)

        # Build the base query
        query = model_class.query

        # Apply search filter (fuzzy match on name and purpose)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                name_column.ilike(search_pattern)
                | purpose_column.ilike(search_pattern)
            )

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if sort_by not in ALLOWED_SORT_BY:
            sort_by = "id"
        if sort_order not in ALLOWED_SORT_ORDER:
            sort_order = "asc"

        sort_column = name_column if sort_by == "name" else id_column
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        # Calculate total pages
        pages = ceil(total / per_page) if total > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @staticmethod
    def parse_query_params(args: Dict[str, str]) -> Dict[str, Any]:
        """Parse and validate query parameters from request args.

        Args:
            args: The request.args MultiDict.

        Returns:
            A dict with sanitized query parameters.
        """
        try:
            page = int(args.get("page", DEFAULT_PAGE))
        except (ValueError, TypeError):
            page = DEFAULT_PAGE

        try:
            per_page = int(args.get("per_page", DEFAULT_PER_PAGE))
        except (ValueError, TypeError):
            per_page = DEFAULT_PER_PAGE

        search = args.get("search", None)
        if search is not None:
            search = search.strip()
            if not search:
                search = None

        sort_by = args.get("sort_by", "id")
        if sort_by not in ALLOWED_SORT_BY:
            sort_by = "id"

        sort_order = args.get("sort_order", "asc")
        if sort_order not in ALLOWED_SORT_ORDER:
            sort_order = "asc"

        return {
            "page": page,
            "per_page": per_page,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
