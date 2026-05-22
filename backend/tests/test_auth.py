import pytest

pytestmark = pytest.mark.django_db


def test_obtain_token(user, unauth_client):
    resp = unauth_client.post(
        '/api/auth/token/',
        {'username': 'testuser', 'password': 'testpass123'},
        format='json',
    )
    assert resp.status_code == 200
    assert 'access' in resp.data
    assert 'refresh' in resp.data


def test_refresh_token(user, unauth_client):
    resp = unauth_client.post(
        '/api/auth/token/',
        {'username': 'testuser', 'password': 'testpass123'},
        format='json',
    )
    resp2 = unauth_client.post(
        '/api/auth/token/refresh/',
        {'refresh': resp.data['refresh']},
        format='json',
    )
    assert resp2.status_code == 200
    assert 'access' in resp2.data


def test_reject_unauthenticated(unauth_client):
    resp = unauth_client.get('/api/habits/')
    assert resp.status_code == 401


def test_reject_invalid_token(unauth_client):
    unauth_client.credentials(HTTP_AUTHORIZATION='Bearer bad.token.value')
    resp = unauth_client.get('/api/habits/')
    assert resp.status_code == 401
