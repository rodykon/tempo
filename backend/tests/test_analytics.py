import datetime

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from habits.models import Habit, HabitDailyRecord, HabitTiming

pytestmark = pytest.mark.django_db

# Every test in this file runs against a frozen "now" instead of the real
# wall clock. Multi-day / week-boundary math (period_start_for, "N days
# ago") is only deterministic if "today" is fixed -- otherwise a test that
# happens to run on a Sunday or Monday can silently cross a week boundary
# it didn't intend to. 2026-06-17 is a Wednesday, 3 days into its week
# (Sun 2026-06-14 .. Sat 2026-06-20), which gives every test room for
# "N days ago" without crossing into the previous week unless a test
# deliberately wants to (e.g. test_backfills_missed_days does, safely,
# because daily habits don't care about week boundaries at all).
NOW = datetime.datetime(2026, 6, 17, 12, 0, tzinfo=datetime.timezone.utc)
TODAY = NOW.date()
WEEK_START = TODAY - datetime.timedelta(days=(TODAY.weekday() + 1) % 7)  # Sunday 2026-06-14


def days_ago(n):
    return TODAY - datetime.timedelta(days=n)


@pytest.fixture(autouse=True)
def frozen_time(monkeypatch):
    monkeypatch.setattr('django.utils.timezone.now', lambda: NOW)


def make_daily(api_client, time=30):
    resp = api_client.post('/api/habits/', {'name': 'Read', 'period': 'daily', 'time': time}, format='json')
    assert resp.status_code == 201
    return resp.data


def make_weekly(api_client, time=180):
    resp = api_client.post('/api/habits/', {'name': 'Exercise', 'period': 'weekly', 'time': time}, format='json')
    assert resp.status_code == 201
    return resp.data


# --- Collection (AC 1) ------------------------------------------------------

def test_no_record_before_day_ends(api_client):
    habit = make_daily(api_client)
    resp = api_client.get(f'/api/timing/{habit["id"]}/')
    assert resp.status_code == 200
    assert HabitDailyRecord.objects.count() == 0
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    assert timing.last_recorded_date == days_ago(1)  # creation baseline, untouched


def test_daily_record_written_on_rollover(api_client):
    habit = make_daily(api_client)  # time=30 -> budget 1800
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.period_start = days_ago(1)
    timing.time_remaining = 100
    timing.last_recorded_date = days_ago(2)
    timing.save()

    resp = api_client.get(f'/api/timing/{habit["id"]}/')
    assert resp.status_code == 200

    record = HabitDailyRecord.objects.get(habit_id=habit['id'], date=days_ago(1))
    assert record.time_remaining == 100
    assert record.time_spent == 1700
    assert record.time_budget == 1800

    timing.refresh_from_db()
    assert timing.last_recorded_date == days_ago(1)


def test_record_captures_pre_reset_value(api_client):
    habit = make_daily(api_client)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.period_start = days_ago(1)
    timing.time_remaining = 100
    timing.last_recorded_date = days_ago(2)
    timing.save()

    resp = api_client.get(f'/api/timing/{habit["id"]}/')
    assert resp.data['time_remaining'] == 1800  # response reflects the post-reset value

    record = HabitDailyRecord.objects.get(habit_id=habit['id'], date=days_ago(1))
    assert record.time_remaining == 100  # but the record holds the pre-reset value


def test_collection_is_idempotent(api_client):
    habit = make_daily(api_client)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.period_start = days_ago(1)
    timing.time_remaining = 100
    timing.last_recorded_date = days_ago(2)
    timing.save()

    api_client.get(f'/api/timing/{habit["id"]}/')
    api_client.get(f'/api/timing/{habit["id"]}/')

    records = HabitDailyRecord.objects.filter(habit_id=habit['id'], date=days_ago(1))
    assert records.count() == 1
    assert records.first().time_spent == 1700


def test_weekly_habit_records_daily_without_resetting(api_client):
    habit = make_weekly(api_client, time=180)
    budget = 180 * 60
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(2)
    timing.time_remaining = budget - 600
    timing.save()

    resp = api_client.get(f'/api/timing/{habit["id"]}/')
    assert resp.status_code == 200

    record = HabitDailyRecord.objects.get(habit_id=habit['id'], date=days_ago(1))
    assert record.time_spent == 600

    timing.refresh_from_db()
    assert timing.period_start == WEEK_START  # untouched -- no reset for a weekly habit mid-week
    assert timing.time_remaining == budget - 600


def test_weekly_uses_previous_day_baseline(api_client):
    habit = make_weekly(api_client, time=180)
    budget = 180 * 60
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(2)
    timing.last_recorded_remaining = budget - 500  # already 500s spent as of 2 days ago
    timing.time_remaining = budget - 800  # 800s spent in total as of end of yesterday
    timing.save()

    api_client.get(f'/api/timing/{habit["id"]}/')

    record = HabitDailyRecord.objects.get(habit_id=habit['id'], date=days_ago(1))
    assert record.time_spent == 300  # day-over-day delta (800-500), not budget-(budget-800)=800


def test_backfills_missed_days(api_client):
    habit = make_daily(api_client)  # budget 1800
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.period_start = days_ago(3)
    timing.time_remaining = 200
    timing.last_recorded_date = days_ago(4)
    timing.save()

    api_client.get(f'/api/timing/{habit["id"]}/')

    records = list(HabitDailyRecord.objects.filter(habit_id=habit['id']).order_by('date'))
    assert [r.date for r in records] == [days_ago(3), days_ago(2), days_ago(1)]
    assert records[0].time_remaining == 200  # the real remaining, carried from before the gap
    assert records[0].time_spent == 1600
    assert records[1].time_remaining == 1800  # fully idle days: untouched budget
    assert records[1].time_spent == 0
    assert records[2].time_remaining == 1800
    assert records[2].time_spent == 0


def test_running_timer_counted_to_end_of_day(api_client):
    habit = make_daily(api_client, time=120)  # budget 7200
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.period_start = days_ago(1)
    timing.time_remaining = 7200
    timing.started_at = datetime.datetime.combine(
        days_ago(1), datetime.time(23, 0), tzinfo=datetime.timezone.utc
    )
    timing.last_recorded_date = days_ago(2)
    timing.save()

    api_client.get(f'/api/timing/{habit["id"]}/')

    record = HabitDailyRecord.objects.get(habit_id=habit['id'], date=days_ago(1))
    assert record.time_remaining == 3600  # 7200 - 3600s elapsed (23:00 -> midnight, exactly)


def test_spent_clamped_at_zero_and_budget(api_client):
    habit = make_weekly(api_client, time=180)
    budget = 180 * 60
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(2)
    timing.last_recorded_remaining = 500  # low baseline from 2 days ago
    timing.time_remaining = budget + 200  # bumped above budget (e.g. a manual timing edit)
    timing.save()

    api_client.get(f'/api/timing/{habit["id"]}/')

    record = HabitDailyRecord.objects.get(habit_id=habit['id'], date=days_ago(1))
    assert record.time_spent == 0  # never negative
    assert record.time_remaining == budget  # capped at budget, not stored as budget+200


def test_records_are_scoped_and_cascade(api_client):
    habit = make_daily(api_client)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.period_start = days_ago(1)
    timing.time_remaining = 100
    timing.last_recorded_date = days_ago(2)
    timing.save()
    timing.check_and_reset()

    record = HabitDailyRecord.objects.get(habit_id=habit['id'])
    assert record.user_id == timing.habit.user_id

    other_user = User.objects.create_user(username='other_scoped', password='pw123456')
    assert HabitDailyRecord.objects.filter(user=other_user).count() == 0

    Habit.objects.get(id=habit['id']).delete()
    assert HabitDailyRecord.objects.filter(habit_id=habit['id']).count() == 0


# --- Analytics endpoint (AC 2 data) -----------------------------------------

def test_analytics_overall_and_per_habit(api_client):
    daily = make_daily(api_client, time=30)  # budget 1800
    weekly = make_weekly(api_client, time=180)  # budget 10800
    daily_timing = HabitTiming.objects.get(habit_id=daily['id'])
    daily_timing.last_recorded_date = days_ago(1)
    daily_timing.save()
    weekly_timing = HabitTiming.objects.get(habit_id=weekly['id'])
    weekly_timing.last_recorded_date = days_ago(1)
    weekly_timing.save()
    user = daily_timing.habit.user

    HabitDailyRecord.objects.create(
        user=user, habit_id=daily['id'], date=days_ago(2), period='daily',
        period_start=days_ago(2), time_budget=1800, time_remaining=800, time_spent=1000,
    )
    HabitDailyRecord.objects.create(
        user=user, habit_id=daily['id'], date=days_ago(1), period='daily',
        period_start=days_ago(1), time_budget=1800, time_remaining=0, time_spent=1800,
    )
    # Two days recorded within the SAME week -> one budget counted once, not twice.
    HabitDailyRecord.objects.create(
        user=user, habit_id=weekly['id'], date=days_ago(2), period='weekly',
        period_start=WEEK_START, time_budget=10800, time_remaining=10500, time_spent=300,
    )
    HabitDailyRecord.objects.create(
        user=user, habit_id=weekly['id'], date=days_ago(1), period='weekly',
        period_start=WEEK_START, time_budget=10800, time_remaining=10200, time_spent=300,
    )

    resp = api_client.get('/api/analytics/')
    assert resp.status_code == 200
    data = resp.data

    daily_row = next(h for h in data['habits'] if h['habit_id'] == daily['id'])
    assert daily_row['time_spent'] == 2800
    assert daily_row['time_planned'] == 3600
    assert daily_row['percentage'] == round(100 * 2800 / 3600, 1)

    weekly_row = next(h for h in data['habits'] if h['habit_id'] == weekly['id'])
    assert weekly_row['time_spent'] == 600
    assert weekly_row['time_planned'] == 10800
    assert weekly_row['percentage'] == round(100 * 600 / 10800, 1)

    assert data['overall']['time_spent'] == 3400
    assert data['overall']['time_planned'] == 14400
    assert data['overall']['percentage'] == round(100 * 3400 / 14400, 1)


def test_analytics_empty_returns_zeroes(api_client):
    make_daily(api_client)
    make_weekly(api_client)

    resp = api_client.get('/api/analytics/')
    assert resp.status_code == 200
    data = resp.data
    assert data['overall'] == {'time_planned': 0, 'time_spent': 0, 'percentage': 0.0}
    assert len(data['habits']) == 2
    for row in data['habits']:
        assert row['time_planned'] == 0
        assert row['time_spent'] == 0
        assert row['percentage'] == 0.0
        assert row['week'] is None


def test_analytics_weekly_chart_payload(api_client):
    habit = make_weekly(api_client, time=180)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(1)
    timing.save()
    user = timing.habit.user
    budget = 180 * 60

    spent_by_date = {
        WEEK_START: 100,
        WEEK_START + datetime.timedelta(days=2): 200,
        WEEK_START + datetime.timedelta(days=3): 300,
    }
    for date, spent in spent_by_date.items():
        HabitDailyRecord.objects.create(
            user=user, habit_id=habit['id'], date=date, period='weekly',
            period_start=WEEK_START, time_budget=budget, time_remaining=budget - spent, time_spent=spent,
        )

    resp = api_client.get('/api/analytics/')
    week = next(h for h in resp.data['habits'] if h['habit_id'] == habit['id'])['week']
    assert week['period_start'] == WEEK_START.isoformat()
    assert len(week['days']) == 7
    assert [d['weekday'] for d in week['days']] == ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    by_date = {d['date']: d['time_spent'] for d in week['days']}
    assert by_date[WEEK_START.isoformat()] == 100
    assert by_date[(WEEK_START + datetime.timedelta(days=2)).isoformat()] == 200
    assert by_date[(WEEK_START + datetime.timedelta(days=3)).isoformat()] == 300
    assert by_date[(WEEK_START + datetime.timedelta(days=1)).isoformat()] == 0
    assert by_date[(WEEK_START + datetime.timedelta(days=4)).isoformat()] == 0


def test_analytics_daily_habit_has_no_week(api_client):
    habit = make_daily(api_client)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(1)
    timing.save()
    HabitDailyRecord.objects.create(
        user=timing.habit.user, habit_id=habit['id'], date=days_ago(1), period='daily',
        period_start=days_ago(1), time_budget=1800, time_remaining=0, time_spent=1800,
    )

    resp = api_client.get('/api/analytics/')
    row = next(h for h in resp.data['habits'] if h['habit_id'] == habit['id'])
    assert row['week'] is None


def test_analytics_isolated_between_users(api_client):
    habit = make_daily(api_client)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(1)
    timing.save()
    HabitDailyRecord.objects.create(
        user=timing.habit.user, habit_id=habit['id'], date=days_ago(1), period='daily',
        period_start=days_ago(1), time_budget=1800, time_remaining=0, time_spent=1800,
    )

    other_user = User.objects.create_user(username='other_isolated', password='pw123456')
    other_client = APIClient()
    other_client.force_authenticate(user=other_user)

    resp = other_client.get('/api/analytics/')
    assert resp.status_code == 200
    assert resp.data['habits'] == []
    assert resp.data['overall']['time_spent'] == 0


def test_analytics_requires_auth(unauth_client):
    assert unauth_client.get('/api/analytics/').status_code == 401
    assert unauth_client.delete('/api/analytics/').status_code == 401


# --- Reset (AC 2 reset button) ----------------------------------------------

def test_reset_deletes_only_own_records(api_client):
    habit = make_daily(api_client)
    timing = HabitTiming.objects.get(habit_id=habit['id'])
    timing.last_recorded_date = days_ago(1)
    timing.save()
    user = timing.habit.user
    HabitDailyRecord.objects.create(
        user=user, habit_id=habit['id'], date=days_ago(1), period='daily',
        period_start=days_ago(1), time_budget=1800, time_remaining=0, time_spent=1800,
    )

    other_user = User.objects.create_user(username='other_reset', password='pw123456')
    other_habit = Habit.objects.create(user=other_user, name='X', period='daily', time=15)
    HabitDailyRecord.objects.create(
        user=other_user, habit=other_habit, date=days_ago(1), period='daily',
        period_start=days_ago(1), time_budget=900, time_remaining=0, time_spent=900,
    )

    resp = api_client.delete('/api/analytics/')
    assert resp.status_code == 204
    assert HabitDailyRecord.objects.filter(user=user).count() == 0
    assert HabitDailyRecord.objects.filter(user=other_user).count() == 1

    resp = api_client.get('/api/analytics/')
    assert resp.data['overall']['time_spent'] == 0


def test_recording_resumes_correctly_after_reset(api_client, monkeypatch):
    habit = make_daily(api_client)  # budget 1800
    timing = HabitTiming.objects.get(habit_id=habit['id'])

    api_client.get(f'/api/timing/{habit["id"]}/')  # fast-path catch-up, nothing to record yet
    api_client.delete('/api/analytics/')  # reset -- no records exist yet, just exercises the path

    timing.refresh_from_db()
    assert timing.last_recorded_date == days_ago(1)  # baseline survives the reset

    tomorrow = NOW + datetime.timedelta(days=1)
    monkeypatch.setattr('django.utils.timezone.now', lambda: tomorrow)
    timing.refresh_from_db()
    timing.time_remaining = 1000
    timing.save()

    resp = api_client.get(f'/api/timing/{habit["id"]}/')
    assert resp.status_code == 200

    records = list(HabitDailyRecord.objects.filter(habit_id=habit['id']))
    assert len(records) == 1
    assert records[0].date == TODAY  # the day that just completed
    assert records[0].time_spent == 800  # 1800 - 1000, correctly using the surviving baseline

    timing.refresh_from_db()
    assert timing.last_recorded_date == TODAY
    assert timing.last_recorded_remaining == 1000
