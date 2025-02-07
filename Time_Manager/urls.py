from django.urls import path
from . import views
from .views import (
    RoutineView, GoalsView, YearlyGoalView, MonthlyGoalView, WeeklyGoalView, DayGoalView, DailyGoalView, DeleteGoalView, DeleteRoutineView, EventsView
)

urlpatterns = [
    path('schedule/events/', views.get_events, name='get-events'),
    path("schedule/", views.ScheduleView, name="scheduller"),
    path("dashboard/", views.DashboardView, name="tm_dashboard"),
    path('routines/', RoutineView.as_view(), name='routine'),
    path('routines/<int:routine_id>/', RoutineView.as_view(), name='edit_routine'),
    path('goals/', GoalsView.as_view(), name='goals'),
    path('goals/create/', views.CreateGoalsView.as_view(), name='create_goal'),
    path('goals/edit/<int:goal_id>/', views.CreateGoalsView.as_view(), name='edit_goal'),
    path('goals/yearly/create/', YearlyGoalView.as_view(), name='create_yearly_goal'),
    path('goals/yearly/edit/<int:goal_id>/', YearlyGoalView.as_view(), name='edit_yearly_goal'),
    path('goals/monthly/create/', MonthlyGoalView.as_view(), name='create_monthly_goal'),
    path('goals/monthly/edit/<int:goal_id>/', MonthlyGoalView.as_view(), name='edit_monthly_goal'),
    path('goals/weekly/create/', WeeklyGoalView.as_view(), name='create_weekly_goal'),
    path('goals/weekly/edit/<int:goal_id>/', WeeklyGoalView.as_view(), name='edit_weekly_goal'),
    path('goals/day/create/', DayGoalView.as_view(), name='create_day_goal'),
    path('goals/day/edit/<int:goal_id>/', DayGoalView.as_view(), name='edit_day_goal'),
    path('goals/daily/create/', DailyGoalView.as_view(), name='create_daily_goal'),
    path('goals/daily/edit/<int:goal_id>/', DailyGoalView.as_view(), name='edit_daily_goal'),
    path('goals/delete/<str:goal_type>/<int:goal_id>/', DeleteGoalView.as_view(), name='delete_goal'),
    path('routines/delete/<int:routine_id>/', DeleteRoutineView.as_view(), name='delete_routine'),
    path('add/', EventsView.as_view(), name='add_event'),
]