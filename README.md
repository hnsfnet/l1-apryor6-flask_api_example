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




## System overview & health

Two operational endpoints make it easy to see the state of the system right
after starting the service, without querying the database or clicking through
each resource by hand.

### `GET /api/overview`

Returns counts for every resource (`widget`, `fizzbar`, `fizzbaz`, `doodad`,
`whatsit`) plus the most recent record's basic info for each. The shape is
stable even on an empty database — `latest` is simply `null` (not an object of
null fields) and counts are `0`, so the response is always safe to render.

```
curl http://localhost:5000/api/overview/
```

```json
{
  "total": 3,
  "resources": {
    "widget":  {"count": 2, "latest": {"id": 2, "name": "Gadget", "purpose": "demo"}},
    "fizzbar": {"count": 1, "latest": {"id": 1, "name": "Foo", "purpose": "demo"}},
    "fizzbaz": {"count": 0, "latest": null},
    "doodad":  {"count": 0, "latest": null},
    "whatsit": {"count": 0, "latest": null}
  }
}
```

The resource list lives in a single registry (`OverviewService.RESOURCES`) and
the per-resource counting/latest logic is shared via `QueryService.summarize`,
so exposing a new module is a one-line change.

### `GET /health`

Now reports a basic database connectivity probe and the list of registered
resource modules, so environment issues can be spotted without digging through
logs.

```
curl http://localhost:5000/health
```

```json
{
  "status": "healthy",
  "database": "connected",
  "modules": ["widget", "fizzbar", "fizzbaz", "doodad", "whatsit"]
}
```

`database` reports `"disconnected"` (instead of erroring) if the connectivity
probe fails.




## Running tests

To run the test suite, simply pip install it and run from the root directory like so

```
pip install pytest
pytest
```

