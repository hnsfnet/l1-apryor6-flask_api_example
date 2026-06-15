from typing import Any, Dict, List, Sequence

from app import db


class BulkService:
    """Reusable helpers for bulk create / delete on a SQLAlchemy model.

    The resources in this project (widget, doodad, ...) share an identical
    shape, so rather than re-implementing the per-item success/failure
    bookkeeping in every module, each service can delegate to these helpers
    and get a consistent, partial-failure-aware result.

    Both helpers are *best effort per item*: valid items are persisted even
    when other items in the same request are rejected. Nothing is silently
    swallowed and nothing forces an all-or-nothing write.
    """

    @staticmethod
    def _validate(attrs: Any, required_fields: Sequence[str]):
        """Return an error string when ``attrs`` cannot be created, else None."""
        if not isinstance(attrs, dict):
            return f"Expected an object, got {type(attrs).__name__}"
        missing = [field for field in required_fields if attrs.get(field) is None]
        if missing:
            return f"Missing required field(s): {', '.join(missing)}"
        return None

    @staticmethod
    def bulk_create(
        model, items: Sequence[Any], required_fields: Sequence[str]
    ) -> Dict[str, Any]:
        """Create many ``model`` rows in one go.

        Each item is validated and inserted inside its own savepoint, so a
        single bad row (failed validation or a database error such as a
        duplicate key) is reported without rolling back the rows that did
        succeed.

        Returns a dict with ``succeeded`` (the created model instances),
        ``failed`` (``{index, item, error}`` per rejected item) and the
        ``success_count`` / ``failure_count`` tallies.
        """
        succeeded: List[Any] = []
        failed: List[Dict[str, Any]] = []

        for index, attrs in enumerate(items or []):
            error = BulkService._validate(attrs, required_fields)
            if error is not None:
                failed.append({"index": index, "item": attrs, "error": error})
                continue
            try:
                with db.session.begin_nested():
                    instance = model(
                        **{field: attrs[field] for field in required_fields}
                    )
                    db.session.add(instance)
                succeeded.append(instance)
            except Exception as exc:  # noqa: B902 - surface any per-row failure
                failed.append({"index": index, "item": attrs, "error": str(exc)})

        db.session.commit()

        return {
            "succeeded": succeeded,
            "failed": failed,
            "success_count": len(succeeded),
            "failure_count": len(failed),
        }

    @staticmethod
    def bulk_delete(model, id_column, ids: Sequence[Any]) -> Dict[str, Any]:
        """Delete many ``model`` rows by id in one go.

        Ids that do not resolve to a row (never existed, or were already
        removed earlier in the same request because they were passed twice)
        are reported under ``not_found`` rather than raising.

        Returns a dict with ``requested`` (the ids as received), ``deleted``,
        ``not_found`` and the ``success_count`` / ``failure_count`` tallies.
        """
        requested: List[Any] = list(ids or [])
        deleted: List[Any] = []
        not_found: List[Any] = []

        for raw_id in requested:
            instance = model.query.filter(id_column == raw_id).first()
            if instance is None:
                not_found.append(raw_id)
                continue
            db.session.delete(instance)
            deleted.append(raw_id)

        db.session.commit()

        return {
            "requested": requested,
            "deleted": deleted,
            "not_found": not_found,
            "success_count": len(deleted),
            "failure_count": len(not_found),
        }
