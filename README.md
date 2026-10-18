# Questionnaire App

A Django web app for building questionnaires in the browser. Each questionnaire is stored and exported as a JSON
document that follows a documented JSON Schema. See [docs/questionnaire-format.md](docs/questionnaire-format.md).

## Run the server

Requires Python 3.12+. Run these from the project root (the folder containing `manage.py`).

**1. Install the dependencies** (first time only):

```bash
pip install -r requirements.txt
```

**2. Create the database** (first time, and again after pulling new migrations):

```bash
python manage.py migrate
```

**3. Start the server:**

```bash
python manage.py runserver
```

Leave it running and stop it with `Ctrl+C`. To use a different port, add it at the end: `python manage.py runserver 8080`.

## Test the app

With the server running, open these in your browser:

| URL | What you'll see |
|---|---|
| http://127.0.0.1:8000/ | Questionnaire list, the place to start |
| http://127.0.0.1:8000/new/ | Builder for a new questionnaire |
| http://127.0.0.1:8000/api/questionnaires/ | The API in the browser (JSON of every saved questionnaire) |
| http://127.0.0.1:8000/api/schema/questionnaire-1.0.json | The JSON Schema |
| http://127.0.0.1:8000/admin/ | Django admin (run `python manage.py createsuperuser` first) |

A quick check:

1. Go to http://127.0.0.1:8000/new/.
2. Enter a title. The ID fills in automatically.
3. Pick a question type, click **Add question** and fill in the question text. Do this a few times.
4. Click **Save**. A **Download JSON** button appears and gives you the `.json` file.
5. Go back to http://127.0.0.1:8000/. Your questionnaire is in the list.

To see validation working, give two questions the same ID and click **Save**. The error appears under the button.

## What's here

| Path | Purpose |
|---|---|
| `questionnaires/schema/questionnaire-1.0.schema.json` | The JSON Schema for the format |
| `questionnaires/validation.py` | Schema validation plus the extra rules (unique ids, min < max, …) |
| `questionnaires/models.py` | `Questionnaire` model: the document lives in a `JSONField` |
| `questionnaires/views.py`, `serializers.py` | REST API (Django REST Framework) and the HTML pages |
| `questionnaires/static/questionnaires/builder.js` | Browser builder (plain JavaScript, no build step) |
| `docs/questionnaire-format.md` | Human-readable spec of the format |

## Pages and API

| URL | |
|---|---|
| `/` | List of questionnaires |
| `/new/`, `/<pk>/edit/` | Builder |
| `GET/POST /api/questionnaires/` | List / create. Body: `{"data": <questionnaire document>}` |
| `GET/PUT/PATCH/DELETE /api/questionnaires/<pk>/` | Read / update / delete |
| `GET /api/questionnaires/<pk>/export/` | Download as `<id>.json` |
| `GET /api/schema/questionnaire-1.0.json` | The JSON Schema |
| `/admin/` | Django admin (`python manage.py createsuperuser` first) |

Invalid documents are rejected with `400` and a list of messages such as
`questions[1].id: duplicate question id 'q1'`.

## Tests

```bash
python manage.py test
```

## Not done yet

- **No user accounts:** the API allows anonymous access (`AllowAny` in `config/settings.py`). Add authentication
  before exposing the app beyond your machine.
- **Production settings:** set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS`.
- **Responses:** the app only creates questionnaires. It doesn't collect answers.
