# Running the Tests

## Setup

Install the test dependencies (once, with your venv active):

```bash
pip install pytest pytest-django
```

## Running all tests

```bash
cd backend
pytest
```

## Running a single test file

```bash
cd backend
pytest tests/test_habits.py
```

## Running a single test

```bash
cd backend
pytest tests/test_habits.py::test_patch_habit
```

## Test files

| File | What it covers |
|------|----------------|
| `tests/test_auth.py` | JWT obtain/refresh, unauthenticated and invalid-token rejection |
| `tests/test_habits.py` | Habit CRUD, validation, per-user isolation |
| `tests/test_timing.py` | Timer start/pause, period reset (daily and weekly) |
| `tests/test_models.py` | Unit tests for `HabitTiming` model methods |
| `tests/test_nginx_config.py` | nginx vhost config serves the app domain (server names, redirect, TLS cert paths) |

## Notes

- Tests use Django's test database — no live server or pre-existing data needed.
- `pytest.ini` in `backend/` sets `DJANGO_SETTINGS_MODULE = tempo.settings` automatically.
