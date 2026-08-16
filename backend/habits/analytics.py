import datetime
from collections import defaultdict

from .models import Habit, HabitDailyRecord

_WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _percentage(spent, planned):
    if not planned:
        return 0.0
    return round(100 * spent / planned, 1)


def _week_payload(period_start, records_for_period):
    by_date = {r.date: r.time_spent for r in records_for_period}
    days = []
    for offset in range(7):
        day = period_start + datetime.timedelta(days=offset)
        days.append({
            'date': day.isoformat(),
            'weekday': _WEEKDAY_LABELS[day.weekday()],
            'time_spent': by_date.get(day, 0),
        })
    return {'period_start': period_start.isoformat(), 'days': days}


def build_analytics(user):
    habits = Habit.objects.filter(user=user).order_by('id')
    records_by_habit = defaultdict(list)
    for record in HabitDailyRecord.objects.filter(user=user).order_by('date'):
        records_by_habit[record.habit_id].append(record)

    habit_rows = []
    for habit in habits:
        records = records_by_habit.get(habit.id, [])

        time_spent = sum(r.time_spent for r in records)
        # One budget per distinct period_start, taken from that group's
        # latest-dated record (records are ordered by date, so later
        # records for the same period_start simply overwrite here).
        budget_by_period = {r.period_start: r.time_budget for r in records}
        time_planned = sum(budget_by_period.values())
        percentage = _percentage(time_spent, time_planned)

        week = None
        if habit.period == Habit.WEEKLY and records:
            latest_period_start = records[-1].period_start
            records_for_period = [r for r in records if r.period_start == latest_period_start]
            week = _week_payload(latest_period_start, records_for_period)

        habit_rows.append({
            'habit_id': habit.id,
            'name': habit.name,
            'period': habit.period,
            'time_planned': time_planned,
            'time_spent': time_spent,
            'percentage': percentage,
            'week': week,
        })

    overall_planned = sum(row['time_planned'] for row in habit_rows)
    overall_spent = sum(row['time_spent'] for row in habit_rows)

    return {
        'overall': {
            'time_planned': overall_planned,
            'time_spent': overall_spent,
            'percentage': _percentage(overall_spent, overall_planned),
        },
        'habits': habit_rows,
    }
