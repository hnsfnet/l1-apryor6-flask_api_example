# Example of a scalable Flask API

![The site](docs/site.png)

A sample project showing how to build a scalable, maintainable, modular Flask API with a heavy emphasis on testing.

_This is an example project using the structure proposed in [this blog post](https://apryor6.github.io/2019-05-20-flask-api-example/)._


## Running the app

Preferably, first create a virtualenv and activate it, perhaps with the following command:

```
virtualenv -p python3 venv
source venv/bin/activate
```

Next, run

```
pip install -r requirements.txt
```

to get the dependencies.

Next, initialize the database

```
python manage.py seed_db
```

Type "Y" to accept the message (which is just there to prevent you accidentally deleting things -- it's just a local SQLite database)

Finally run the app with

```
python wsgi.py
```

Navigate to the posted URL in your terminal to be greeted with Swagger, where you can test out the API.


## System Overview & Health Endpoints

### GET /api/overview/

Returns a summary of all registered resource modules, including:
- **count**: total number of records in the database for each resource type
- **latest**: the most recent record (by primary key) with `id`, `name`, and `purpose` fields; `null` if no records exist

Example response:

```json
{
  "resources": {
    "widget":  { "count": 3, "latest": { "id": 3, "name": "Pizza Oven", "purpose": "Bake delicious pizza" } },
    "fizzbar": { "count": 3, "latest": { "id": 3, "name": "Pizza Oven", "purpose": "Bake delicious pizza" } },
    "fizzbaz": { "count": 0, "latest": null },
    "doodad":  { "count": 3, "latest": { "id": 3, "name": "Pizza Oven", "purpose": "Bake delicious pizza" } },
    "whatsit": { "count": 0, "latest": null }
  }
}
```

This endpoint is safe to call even when the database is empty — it will return counts of 0 and `null` for latest without errors.

### GET /health

Returns system health information including:
- **status**: `"healthy"` or `"degraded"`
- **database**: `"connected"` or `"unavailable"`
- **modules**: list of registered Flask blueprints
- **namespaces**: list of registered flask-restx namespaces (API modules)

Example response:

```json
{
  "status": "healthy",
  "database": "connected",
  "modules": ["other_api"],
  "namespaces": ["Widget", "Fizzbar", "Fizzbaz", "Doodad", "Whatsit", "Overview"]
}
```

### Adding New Modules to the Overview

The overview uses the shared `QueryService.get_resource_summary()` method from `app/shared/query/service.py`. To add a new resource module to the overview, simply add a descriptor dict to `_get_resource_descriptors()` in `app/shared/overview/controller.py`:

```python
{"name": "new_resource", "model": NewResource, "id_col": "new_resource_id"},
```


## Running tests

To run the test suite, simply pip install it and run from the root directory like so

```
pip install pytest
pytest
```

