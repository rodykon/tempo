import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Habit(models.Model):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    PERIOD_CHOICES = [(DAILY, 'Daily'), (WEEKLY, 'Weekly')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    time = models.PositiveIntegerField()  # minutes

    def __str__(self):
        return f"{self.name} ({self.period})"


class HabitTiming(models.Model):
    habit = models.OneToOneField(Habit, on_delete=models.CASCADE, related_name='timing')
    # seconds remaining as of started_at (if running) or last pause/reset
    time_remaining = models.PositiveIntegerField()
    started_at = models.DateTimeField(null=True, blank=True)
    period_start = models.DateField()

    def _current_period_start(self):
        today = timezone.now().date()
        if self.habit.period == Habit.DAILY:
            return today
        return today - datetime.timedelta(days=(today.weekday() + 1) % 7)  # most recent Sunday

    def check_and_reset(self):
        if self.period_start < self._current_period_start():
            self.time_remaining = self.habit.time * 60
            self.started_at = None
            self.period_start = self._current_period_start()
            self.save()

    def computed_time_remaining(self):
        if self.started_at is None:
            return self.time_remaining
        elapsed = int((timezone.now() - self.started_at).total_seconds())
        return max(0, self.time_remaining - elapsed)
