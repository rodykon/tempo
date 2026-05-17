import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_create_daily_habit(api_client):
    resp = api_client.post(
        '/api/habits/',
        {'name': 'Read', 'description': 'Read books', 'period': 'daily', 'time': 30},
        format='json',
    )
    assert resp.status_code == 201
    assert resp.data['name'] == 'Read'
    assert resp.data['period'] == 'daily'
    assert resp.data['time'] == 30


def test_create_weekly_habit(api_client):
    resp = api_client.post(
        '/api/habits/',
        {'name': 'Exercise', 'period': 'weekly', 'time': 180},
        format='json',
    )
    assert resp.status_code == 201
    assert resp.data['period'] == 'weekly'


def test_list_habits(api_client, daily_habit, weekly_habit):
    resp = api_client.get('/api/habits/')
    assert resp.status_code == 200
    assert len(resp.data) == 2


def test_get_habit_by_id(api_client, daily_habit):
    resp = api_client.get(f'/api/habits/{daily_habit["id"]}/')
    assert resp.status_code == 200
    assert resp.data['id'] == daily_habit['id']


def test_patch_habit(api_client, daily_habit):
    resp = api_client.patch(
        f'/api/habits/{daily_habit["id"]}/',
        {'name': 'Read books', 'time': 45},
        format='json',
    )
    assert resp.status_code == 200
    assert resp.data['name'] == 'Read books'
    assert resp.data['time'] == 45


def test_patch_time_resets_timing(api_client, daily_habit):
    # Use some of the budget first, then change the time allocation.
    api_client.put(
        f'/api/timing/{daily_habit["id"]}/',
        {'time_remaining': 500, 'is_running': False},
        format='json',
    )
    api_client.patch(
        f'/api/habits/{daily_habit["id"]}/',
        {'time': 45},
        format='json',
    )
    resp = api_client.get(f'/api/timing/{daily_habit["id"]}/')
    assert resp.data['time_remaining'] == 45 * 60
    assert resp.data['is_running'] is False


def test_patch_name_does_not_reset_timing(api_client, daily_habit):
    api_client.put(
        f'/api/timing/{daily_habit["id"]}/',
        {'time_remaining': 500, 'is_running': False},
        format='json',
    )
    api_client.patch(
        f'/api/habits/{daily_habit["id"]}/',
        {'name': 'Read books'},
        format='json',
    )
    resp = api_client.get(f'/api/timing/{daily_habit["id"]}/')
    assert resp.data['time_remaining'] == 500


def test_delete_habit(api_client, daily_habit):
    resp = api_client.delete(f'/api/habits/{daily_habit["id"]}/')
    assert resp.status_code == 204
    assert api_client.get(f'/api/habits/{daily_habit["id"]}/').status_code == 404


def test_list_empty_after_delete(api_client, daily_habit):
    api_client.delete(f'/api/habits/{daily_habit["id"]}/')
    resp = api_client.get('/api/habits/')
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_time_must_be_positive(api_client):
    resp = api_client.post(
        '/api/habits/',
        {'name': 'Bad', 'period': 'daily', 'time': 0},
        format='json',
    )
    assert resp.status_code == 400


def test_habit_isolation(api_client, daily_habit):
    other = User.objects.create_user(username='other', password='other123')
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    resp = other_client.get('/api/habits/')
    assert resp.status_code == 200
    assert len(resp.data) == 0
