from .service import OverviewService  # noqa

BASE_ROUTE = "overview"


def register_routes(api, app, root="api"):
    from .controller import api as overview_api

    api.add_namespace(overview_api, path=f"/{root}/{BASE_ROUTE}")
