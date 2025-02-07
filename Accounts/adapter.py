from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect

class MyAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # Disable sign-up via social accounts (Google) and auto-login
        return False

    def get_login_redirect_url(self, request):
        return "/betterself/Accounts/dashboard/"

class CustomSocialAccountAdapter(DefaultAccountAdapter):
    def authenticate(self, request, **credentials):
        user = super().authenticate(request, **credentials)
        if user and not user.has_usable_password():
            return redirect("signup")  # Redirect Google users to complete signup
        return user
