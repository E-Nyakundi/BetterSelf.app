from django.urls import path
from .views import (
    FinanceDashboardView,
    FinancialGoalCreateView, FinancialGoalDeleteView, FinancialGoalDetailView,
    FinancialGoalListView, FinancialGoalUpdateView,
)

urlpatterns = [
    path('', FinanceDashboardView.as_view(), name='finance-dashboard'),
    path('goals/', FinancialGoalListView.as_view(), name='financial-goal-list'),
    path('goals/create/', FinancialGoalCreateView.as_view(), name='financial-goal-create'),
    path('goals/<int:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),
    path('goals/<int:pk>/edit/', FinancialGoalUpdateView.as_view(), name='financial-goal-edit'),
    path('goals/<int:pk>/delete/', FinancialGoalDeleteView.as_view(), name='financial-goal-delete'),
]
