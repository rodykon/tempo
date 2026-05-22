from django.contrib import admin

from .models import Habit, HabitTiming

admin.site.register(Habit)
admin.site.register(HabitTiming)
