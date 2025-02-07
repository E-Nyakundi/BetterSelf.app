from django.urls import path,include
from . import views
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path("dashboard/", views.DashboardView, name="dashboard"),
    path("sign-up/", views.SignUpView.as_view(), name="sign-up"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("set-password/", views.set_password, name="set_password"),
]
