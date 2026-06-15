from flask_restx import Namespace, Resource

from .service import OverviewService

api = Namespace(  # noqa
    "Overview", description="Operational summary across all resources"
)


@api.route("/")
class OverviewResource(Resource):
    """Aggregate counts and latest records for every resource module."""

    def get(self):
        """Get an overview of all resources (counts + latest record each)."""

        return OverviewService.get_overview()
