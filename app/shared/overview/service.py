from app.shared.query.service import QueryService

from app.widget.model import Widget
from app.fizz.fizzbar.model import Fizzbar
from app.fizz.fizzbaz.model import Fizzbaz
from app.other_api.doodad.model import Doodad
from app.other_api.whatsit.model import Whatsit


class OverviewService:
    """Builds an operational overview across every registered resource.

    ``RESOURCES`` is the single place to extend this feature: to surface a new
    module in both the overview endpoint and ``/health``, add one
    ``(name, model)`` entry here. The per-resource counting / latest-record
    logic lives in :class:`QueryService`, so nothing is copy-pasted per model.
    """

    RESOURCES = (
        ("widget", Widget),
        ("fizzbar", Fizzbar),
        ("fizzbaz", Fizzbaz),
        ("doodad", Doodad),
        ("whatsit", Whatsit),
    )

    @classmethod
    def module_names(cls):
        """Names of the modules wired into the overview (used by /health)."""
        return [name for name, _ in cls.RESOURCES]

    @classmethod
    def get_overview(cls):
        """Aggregate counts + latest record per resource.

        Always returns the same shape, even for an empty database::

            {
                "total": <int>,
                "resources": {
                    "<name>": {"count": <int>, "latest": {..} | None},
                    ...
                },
            }
        """
        resources = {
            name: QueryService.summarize(model) for name, model in cls.RESOURCES
        }
        total = sum(summary["count"] for summary in resources.values())
        return {"total": total, "resources": resources}
