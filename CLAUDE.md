# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tempo is a time-management habit tracker. Users define habits with a daily or weekly time budget (in minutes); a timer counts down that budget within each period. Unmet time does **not** carry over — periods reset cleanly.

Stack: Django 5 + Django REST Framework + SimpleJWT (backend), React/Vite (frontend, not yet in repo), SQLite (dev).

## Commands

All Django commands run from `backend/`:

```bash
# Run dev server (http://127.0.0.1:8000)
cd backend && python manage.py runserver

# Apply migrations
cd backend && python manage.py migrate

# Create migrations after model changes
cd backend && python manage.py makemigrations

# Create a test user for manual testing
cd backend && python manage.py shell -c \
  "from django.contrib.auth.models import User; User.objects.create_user('testuser', password='testpass123')"

# Run API smoke tests (requires a running server and a testuser)
python test_api.py
```

No linting or test framework is configured yet.

## Architecture

### Data Models (`backend/habits/models.py`)

```
User (Django built-in)
 └─ Habit          (ForeignKey, CASCADE)
     └─ HabitTiming (OneToOne, CASCADE)
```

**Habit**: stores `name`, `description`, `period` (`'daily'`|`'weekly'`), `time` (budget in minutes).

**HabitTiming**: manages timer state.
- `time_remaining` — seconds left as of the last pause/sync
- `started_at` — `DateTimeField`, non-null only when timer is running
- `period_start` — the Sunday (weekly) or today (daily) that began the current period
- `check_and_reset()` — called on every read; resets `time_remaining` to the full budget if the period has rolled over
- `computed_time_remaining()` — subtracts elapsed wall-clock seconds from `time_remaining` when `started_at` is set

### Timer Design

The timer is **client-driven**: the React frontend counts down locally and only syncs to the server on pause or explicit update. The server never pushes timer ticks. On GET the server computes the live value via `computed_time_remaining()`.

### API (`backend/habits/urls.py`, `backend/tempo/urls.py`)

All routes are under `/api/` and require JWT Bearer auth (`IsAuthenticated` is the global default).

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/token/` | Obtain JWT (username + password) |
| POST | `/api/auth/token/refresh/` | Refresh JWT |
| GET/POST | `/api/habits/` | List / create habits |
| GET/PATCH/DELETE | `/api/habits/{id}/` | Retrieve / update / delete |
| GET | `/api/timing/` | List all timings (triggers `check_and_reset`) |
| GET | `/api/timing/{habit_id}/` | Get one timing |
| PUT | `/api/timing/{habit_id}/` | Update timing (`time_remaining`, `is_running`) |
| GET | `/api/analytics/` | Per-user analytics (Big Picture + per-habit stats + weekly chart data); triggers `check_and_reset` on every timing first, same as `/api/timing/` |
| DELETE | `/api/analytics/` | Delete all of this user's `HabitDailyRecord` rows (the "Reset Statistics" button) |

All habit/timing/analytics queries are automatically scoped to `request.user`.

### Period Reset Logic

- **Daily**: resets at midnight UTC (`period_start = today`).
- **Weekly**: resets each Sunday. Formula: `today - timedelta(days=(today.weekday() + 1) % 7)`.
- **Analytics collection** runs as the first statement of `check_and_reset()`, i.e. strictly before a reset can wipe `time_remaining` — `HabitTiming.record_completed_days()` writes one `HabitDailyRecord` per completed day (both daily and weekly habits) using a rolling baseline (`last_recorded_date`/`last_recorded_remaining`) so day-over-day `time_spent` stays correct across resets, backfills up to `MAX_BACKFILL_DAYS` for a long-dormant habit, and is a no-op (no query, no write) once already caught up through yesterday.

### CORS

The backend allows `http://localhost:5173` (Vite dev server).

## Key Files

- `backend/habits/models.py` — core domain logic (timer math, period reset)
- `backend/habits/serializers.py` — HabitSerializer auto-creates HabitTiming on habit creation; HabitTimingSerializer exposes computed fields
- `backend/habits/views.py` — ViewSets; timing views call `check_and_reset()` before returning
- `backend/tempo/settings.py` — JWT auth, CORS, REST framework defaults
- `test_api.py` — end-to-end smoke tests covering auth, CRUD, and timing flows
- `docs/` — methodology and feature spec
