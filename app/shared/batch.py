"""
Shared batch operation utilities for resources with identical structure.

Provides generic batch_create and batch_delete functions that can be reused
across any module whose model follows the (id, name, purpose) pattern.
"""

from typing import List, Tuple, Any, Dict
from app import db


def batch_create(
    model_class,
    items: List[dict],
) -> Tuple[List[Any], List[Dict]]:
    """
    Batch create items for a given model class.

    Each item is validated individually. Valid items are added to the session
    and committed together. Invalid items are recorded with their index and
    error message.

    Args:
        model_class: The SQLAlchemy model class (e.g. Widget, Doodad).
        items: A list of dicts, each with at least 'name' and optionally 'purpose'.

    Returns:
        A tuple of (successful_models, failed_items).
        - successful_models: list of created model instances
        - failed_items: list of dicts like {'index': <int>, 'error': <str>}
    """
    successful = []
    failed = []

    for i, item_data in enumerate(items):
        if not isinstance(item_data, dict):
            failed.append({"index": i, "error": "Item must be a JSON object"})
            continue

        name = item_data.get("name")
        if not name or (isinstance(name, str) and not name.strip()):
            failed.append({"index": i, "error": "Missing required field: name"})
            continue

        try:
            new_item = model_class(
                name=name,
                purpose=item_data.get("purpose", ""),
            )
            db.session.add(new_item)
            db.session.flush()
            successful.append(new_item)
        except Exception as e:
            failed.append({"index": i, "error": str(e)})

    if successful:
        db.session.commit()

    return successful, failed


def batch_delete(
    model_class,
    ids: List[int],
    id_column,
) -> Tuple[List[int], List[Dict]]:
    """
    Batch delete items by their IDs.

    Each ID is looked up individually. Found items are deleted; missing IDs
    are recorded as failures.

    Args:
        model_class: The SQLAlchemy model class.
        ids: A list of integer IDs to delete.
        id_column: The SQLAlchemy column reference for the primary key
                   (e.g. Widget.widget_id).

    Returns:
        A tuple of (successful_ids, failed_items).
        - successful_ids: list of deleted IDs
        - failed_items: list of dicts like {'id': <int>, 'error': <str>}
    """
    successful = []
    failed = []

    for id_val in ids:
        item = model_class.query.filter(id_column == id_val).first()
        if item:
            db.session.delete(item)
            successful.append(id_val)
        else:
            failed.append({"id": id_val, "error": "Not found"})

    if successful:
        db.session.commit()

    return successful, failed
