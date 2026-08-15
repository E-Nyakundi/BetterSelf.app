from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.DashboardView, name="dashboard"),
    path("dashboard/toggle-goal/<int:goal_id>/", views.toggle_daily_goal, name="toggle_daily_goal"),
    path("sign-up/", views.SignUpView.as_view(), name="sign-up"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView, name="logout"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset/<uidb64>/<token>/", views.SetPasswordView.as_view(), name="password-reset-confirm"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
]
