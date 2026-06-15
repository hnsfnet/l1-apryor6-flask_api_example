from .controller import api as overview_api  # noqa

BASE_ROUTE = "overview"


def register_routes(api, app, root="api"):
    api.add_namespace(overview_api, path=f"/{root}/{BASE_ROUTE}")
