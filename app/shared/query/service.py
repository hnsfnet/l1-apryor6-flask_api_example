from sqlalchemy import inspect


class QueryService:
    """Query helpers that are shared across modules."""

    # Basic fields we surface for a "latest record" preview. Every resource
    # model in this project exposes these, so the summary stays generic.
    SUMMARY_FIELDS = ("name", "purpose")

    @staticmethod
    def execute(query):
        return "Success"

    @classmethod
    def summarize(cls, model):
        """Summarize a model for an operational overview.

        Returns a stable shape regardless of whether the table has rows::

            {"count": <int>, "latest": {"id": .., "name": .., "purpose": ..} | None}

        ``latest`` is a single ``None`` (not an object full of null fields) when
        the table is empty, so callers always receive the same keys and can
        render an empty state without special-casing a pile of nulls.

        The primary key is discovered via SQLAlchemy introspection, so adding a
        new module needs no per-model code here -- only an entry in the resource
        registry that calls this helper.
        """
        pk_column = inspect(model).primary_key[0]
        count = model.query.count()
        if count == 0:
            return {"count": 0, "latest": None}

        latest = model.query.order_by(pk_column.desc()).first()
        return {"count": count, "latest": cls._describe(latest, pk_column.name)}

    @classmethod
    def _describe(cls, record, pk_name):
        info = {"id": getattr(record, pk_name)}
        for field in cls.SUMMARY_FIELDS:
            info[field] = getattr(record, field, None)
        return info
