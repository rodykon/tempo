import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def unauth_client():
    return APIClient()


@pytest.fixture
def daily_habit(api_client):
    resp = api_client.post(
        '/api/habits/',
        {'name': 'Read', 'description': 'Read books', 'period': 'daily', 'time': 30},
        format='json',
    )
    return resp.data


@pytest.fixture
def weekly_habit(api_client):
    resp = api_client.post(
        '/api/habits/',
        {'name': 'Exercise', 'period': 'weekly', 'time': 180},
        format='json',
    )
    return resp.data
