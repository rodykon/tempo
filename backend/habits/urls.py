from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('habits', views.HabitViewSet, basename='habit')

urlpatterns = [
    path('', include(router.urls)),
    path('timing/', views.HabitTimingListView.as_view(), name='timing-list'),
    path('timing/<int:habit_id>/', views.HabitTimingDetailView.as_view(), name='timing-detail'),
]
