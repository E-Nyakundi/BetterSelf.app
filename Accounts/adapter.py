from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return settings.LOGIN_REDIRECT_URL

    def get_logout_redirect_url(self, request):
        return settings.LOGOUT_REDIRECT_URL


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user and user.email:
            user.email = user.email.lower()
