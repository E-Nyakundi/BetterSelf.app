from django.urls import path
from . import views

urlpatterns = [
	path("dashboard/", views.DashboardView, name="dashboard"),
	path("sign-up/", views.SignUpView.as_view() , name = "sign-up"),
	path("login/", views.LoginView.as_view(), name="login")
]