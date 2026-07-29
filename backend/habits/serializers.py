import datetime

from django.utils import timezone
from rest_framework import serializers

from .models import Habit, HabitTiming


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ['id', 'name', 'description', 'period', 'time']

    def validate_time(self, value):
        if value <= 0:
            raise serializers.ValidationError("Time must be greater than 0.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        habit = Habit.objects.create(user=user, **validated_data)
        today = timezone.now().date()
        period_start = (
            today - datetime.timedelta(days=(today.weekday() + 1) % 7)
            if habit.period == Habit.WEEKLY
            else today
        )
        HabitTiming.objects.create(
            habit=habit,
            time_remaining=habit.time * 60,
            period_start=period_start,
        )
        return habit

    def update(self, instance, validated_data):
        old_time = instance.time
        new_time = validated_data.get('time')
        habit = super().update(instance, validated_data)
        if new_time is not None and new_time != old_time:
            habit.timing.time_remaining = new_time * 60
            habit.timing.started_at = None
            habit.timing.save()
        return habit


class HabitTimingSerializer(serializers.ModelSerializer):
    habit_id = serializers.IntegerField(source='habit.id', read_only=True)
    time_remaining = serializers.SerializerMethodField()
    is_running = serializers.SerializerMethodField()

    class Meta:
        model = HabitTiming
        fields = ['habit_id', 'time_remaining', 'is_running', 'period_start']

    def get_time_remaining(self, obj):
        return obj.computed_time_remaining()

    def get_is_running(self, obj):
        return obj.started_at is not None


class HabitTimingUpdateSerializer(serializers.Serializer):
    time_remaining = serializers.IntegerField(min_value=0)
    is_running = serializers.BooleanField()
    period_start = serializers.DateField(required=False)
