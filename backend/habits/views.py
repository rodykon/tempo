from django.utils import timezone
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response

from .models import Habit, HabitTiming
from .serializers import HabitSerializer, HabitTimingSerializer, HabitTimingUpdateSerializer


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class HabitTimingListView(generics.ListAPIView):
    serializer_class = HabitTimingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        timings = list(
            HabitTiming.objects.filter(habit__user=self.request.user).select_related('habit')
        )
        for timing in timings:
            timing.check_and_reset()
        return timings


class HabitTimingDetailView(generics.RetrieveAPIView):
    serializer_class = HabitTimingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        timing = HabitTiming.objects.select_related('habit').get(
            habit__id=self.kwargs['habit_id'],
            habit__user=self.request.user,
        )
        timing.check_and_reset()
        return timing

    def put(self, request, habit_id):
        timing = self.get_object()
        serializer = HabitTimingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        timing.time_remaining = data['time_remaining']
        timing.started_at = timezone.now() if data['is_running'] else None
        timing.save()

        return Response(HabitTimingSerializer(timing).data)
