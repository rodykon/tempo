import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

MAX_BACKFILL_DAYS = 31  # bounds the per-request work for a long-dormant habit


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

    # Rolling baseline for daily analytics collection. Null on pre-existing
    # rows (no baseline yet). last_recorded_date is the last day for which a
    # HabitDailyRecord has been written; last_recorded_remaining is the
    # remaining-seconds value that was recorded for it.
    last_recorded_date = models.DateField(null=True, blank=True)
    last_recorded_remaining = models.PositiveIntegerField(null=True, blank=True)

    def _period_start_for(self, day):
        if self.habit.period == Habit.DAILY:
            return day
        return day - datetime.timedelta(days=(day.weekday() + 1) % 7)  # most recent Sunday

    def _current_period_start(self):
        return self._period_start_for(timezone.now().date())

    def _remaining_at(self, when):
        if self.started_at is None or when <= self.started_at:
            return self.time_remaining
        elapsed = int((when - self.started_at).total_seconds())
        return max(0, self.time_remaining - elapsed)

    def _end_of_day(self, day):
        next_day = day + datetime.timedelta(days=1)
        return datetime.datetime.combine(next_day, datetime.time.min, tzinfo=datetime.timezone.utc)

    def record_completed_days(self):
        today = timezone.now().date()
        if self.last_recorded_date is not None:
            start = self.last_recorded_date + datetime.timedelta(days=1)
        else:
            start = self.period_start
        start = max(start, today - datetime.timedelta(days=MAX_BACKFILL_DAYS))

        if start > today - datetime.timedelta(days=1):
            return  # fast path: nothing completed since we last recorded -- no writes

        budget = self.habit.time * 60
        day = start
        while day <= today - datetime.timedelta(days=1):
            period_start = self._period_start_for(day)
            if period_start > self.period_start:
                # A whole period elapsed with no interaction at all -- the
                # habit was never touched during it, so it ends untouched.
                remaining = budget
            else:
                remaining = self._remaining_at(self._end_of_day(day))

            if day == period_start or self.last_recorded_remaining is None:
                baseline = budget
            else:
                baseline = self.last_recorded_remaining
            spent = min(budget, max(0, baseline - remaining))

            HabitDailyRecord.objects.get_or_create(
                habit=self.habit,
                date=day,
                defaults=dict(
                    user=self.habit.user,
                    period=self.habit.period,
                    period_start=period_start,
                    time_budget=budget,
                    time_remaining=min(remaining, budget),
                    time_spent=spent,
                ),
            )
            self.last_recorded_date, self.last_recorded_remaining = day, remaining
            day += datetime.timedelta(days=1)

        self.save()

    def check_and_reset(self):
        self.record_completed_days()
        if self.period_start < self._current_period_start():
            self.time_remaining = self.habit.time * 60
            self.started_at = None
            self.period_start = self._current_period_start()
            self.save()

    def computed_time_remaining(self):
        return self._remaining_at(timezone.now())


class HabitDailyRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_records')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='records')
    date = models.DateField()
    period = models.CharField(max_length=10, choices=Habit.PERIOD_CHOICES)
    period_start = models.DateField()
    time_budget = models.PositiveIntegerField()
    time_remaining = models.PositiveIntegerField()
    time_spent = models.PositiveIntegerField()

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.habit_id} @ {self.date}"
