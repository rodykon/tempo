import datetime

import pytest
from django.utils import timezone

from habits.models import HabitTiming

pytestmark = pytest.mark.django_db


def test_initial_timing(api_client, daily_habit):
    resp = api_client.get(f'/api/timing/{daily_habit["id"]}/')
    assert resp.status_code == 200
    assert resp.data['time_remaining'] == daily_habit['time'] * 60
    assert resp.data['is_running'] is False


def test_list_timings(api_client, daily_habit, weekly_habit):
    resp = api_client.get('/api/timing/')
    assert resp.status_code == 200
    assert len(resp.data) == 2


def test_start_timer(api_client, daily_habit):
    resp = api_client.put(
        f'/api/timing/{daily_habit["id"]}/',
        {'time_remaining': daily_habit['time'] * 60, 'is_running': True},
        format='json',
    )
    assert resp.status_code == 200
    assert resp.data['is_running'] is True


def test_pause_timer(api_client, daily_habit):
    api_client.put(
        f'/api/timing/{daily_habit["id"]}/',
        {'time_remaining': daily_habit['time'] * 60, 'is_running': True},
        format='json',
    )
    resp = api_client.put(
        f'/api/timing/{daily_habit["id"]}/',
        {'time_remaining': 2000, 'is_running': False},
        format='json',
    )
    assert resp.status_code == 200
    assert resp.data['time_remaining'] == 2000
    assert resp.data['is_running'] is False


def test_daily_period_reset(api_client, daily_habit):
    timing = HabitTiming.objects.get(habit_id=daily_habit['id'])
    timing.period_start = timezone.now().date() - datetime.timedelta(days=1)
    timing.time_remaining = 100
    timing.save()

    resp = api_client.get(f'/api/timing/{daily_habit["id"]}/')
    assert resp.status_code == 200
    assert resp.data['time_remaining'] == daily_habit['time'] * 60
    assert resp.data['is_running'] is False


def test_weekly_period_reset(api_client, weekly_habit):
    timing = HabitTiming.objects.get(habit_id=weekly_habit['id'])
    timing.period_start = timing.period_start - datetime.timedelta(weeks=1)
    timing.time_remaining = 100
    timing.save()

    resp = api_client.get(f'/api/timing/{weekly_habit["id"]}/')
    assert resp.status_code == 200
    assert resp.data['time_remaining'] == weekly_habit['time'] * 60
