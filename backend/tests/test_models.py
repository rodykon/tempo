import datetime

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from habits.models import Habit, HabitTiming

pytestmark = pytest.mark.django_db


@pytest.fixture
def habit(db):
    user = User.objects.create_user(username='modeluser', password='pass')
    return Habit.objects.create(user=user, name='Test', period='daily', time=30)


@pytest.fixture
def timing(habit):
    return HabitTiming.objects.create(
        habit=habit,
        time_remaining=habit.time * 60,
        period_start=timezone.now().date(),
    )


def test_computed_time_remaining_paused(timing):
    assert timing.computed_time_remaining() == timing.time_remaining


def test_computed_time_remaining_running(timing):
    timing.started_at = timezone.now() - datetime.timedelta(seconds=60)
    result = timing.computed_time_remaining()
    assert abs(result - (timing.time_remaining - 60)) <= 1  # allow 1s clock skew


def test_computed_time_remaining_clamps_at_zero(timing):
    timing.started_at = timezone.now() - datetime.timedelta(seconds=timing.time_remaining + 100)
    assert timing.computed_time_remaining() == 0


def test_check_and_reset_when_period_expired(timing):
    timing.period_start = timezone.now().date() - datetime.timedelta(days=1)
    timing.time_remaining = 100
    timing.started_at = timezone.now()
    timing.save()

    timing.check_and_reset()

    assert timing.time_remaining == timing.habit.time * 60
    assert timing.started_at is None


def test_check_and_reset_no_op_within_period(timing):
    timing.time_remaining = 100
    timing.save()

    timing.check_and_reset()

    assert timing.time_remaining == 100  # unchanged
