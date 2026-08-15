from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View

from . import dashboard_helpers
from .forms import ProfileForm
from .models import Profile
from Time_Manager.models import DailyGoal


def HomeView(request):
    return render(request, "Accounts/index.html")


@login_required
def DashboardView(request):
    user = request.user
    now = timezone.localtime(timezone.now())
    today = now.date()

    next_up = dashboard_helpers.get_next_up(user, today, now.time())
    todays_focus = dashboard_helpers.get_today_focus(user, today)
    streaks = dashboard_helpers.get_active_streaks(user, today)
    goal_progress = dashboard_helpers.get_goal_progress(user)
    wellbeing = dashboard_helpers.get_wellbeing_rings(user, today)
    recent_activity = dashboard_helpers.get_recent_activity(user)
    finance = dashboard_helpers.get_finance_summary(user)

    context = {
        'today': today,
        'next_up': next_up,
        'todays_focus': todays_focus,
        'streaks': streaks,
        'goal_progress': goal_progress,
        'wellbeing': wellbeing,
        'recent_activity': recent_activity,
        'finance': finance,
    }
    return render(request, "Accounts/dashboard.html", context)


@login_required
def toggle_daily_goal(request, goal_id):
    if request.method != "POST":
        return redirect('dashboard')
    goal = get_object_or_404(
        DailyGoal,
        id=goal_id,
        day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=request.user,
    )
    goal.completed = not goal.completed
    goal.save()
    return redirect('dashboard')


@login_required
def LogoutView(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect('login')


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"email": request.user.email, "title": "New User"},
    )
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            user_email = profile.email.strip().lower()
            if user_email and request.user.email != user_email:
                request.user.email = user_email
                request.user.save(update_fields=['email'])
                profile.email_verified = False
                profile.save(update_fields=['email_verified'])
                messages.success(request, "Profile updated. Your email has changed.")
            else:
                messages.success(request, "Profile updated.")
            return redirect("edit_profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "Accounts/edit_profile.html", {"form": form, "profile": profile})


class SignUpView(View):
    template_name = "Accounts/create_user.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')

        email = request.POST.get("email", "").strip().lower()
        password1 = request.POST.get("password", "")
        password2 = request.POST.get("password_confirm", "")

        errors = []
        if not email:
            errors.append("Email is required.")
        if not password1:
            errors.append("Password is required.")
        if password1 != password2:
            errors.append("Passwords do not match.")
        if len(password1) < 8:
            errors.append("Password must be at least 8 characters.")

        User = get_user_model()
        if not errors and User.objects.filter(email__iexact=email).exists():
            errors.append("An account with this email already exists. Try logging in.")

        if errors:
            return render(request, self.template_name, {"errors": errors, "email": email})

        # Create user
        base_username = (email.split("@")[0] or "user")[:25]
        username = base_username
        suffix = 0
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User.objects.create_user(username=username, email=email, password=password1)
        Profile.objects.get_or_create(
            user=user,
            defaults={"email": email, "title": "New User", "email_verified": False, "auth_provider": "password"},
        )
        login(request, user)
        messages.success(request, "Welcome to LifeApp!")
        return redirect(settings.LOGIN_REDIRECT_URL)


class LoginView(View):
    template_name = "Accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            return render(request, self.template_name, {
                "error": "Email and password are required.",
                "email": email,
            })

        # Try authenticating by email — find the username first
        User = get_user_model()
        try:
            user_obj = User.objects.get(email__iexact=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = email  # fall through to fail naturally

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, self.template_name, {
                "error": "Incorrect email or password.",
                "email": email,
            })

        login(request, user)
        next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
        return redirect(next_url)


class ForgotPasswordView(View):
    template_name = "Accounts/forgot_password.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip()
        form = PasswordResetForm({"email": email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name="registration/password_reset_email.html",
                subject_template_name="registration/password_reset_subject.txt",
            )
        # Always show success to avoid email enumeration
        return render(request, self.template_name, {"sent": True})


class SetPasswordView(View):
    """Handle the password reset link from email."""
    template_name = "Accounts/set_password.html"

    def _get_user(self, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return None, False
        if default_token_generator.check_token(user, token):
            return user, True
        return None, False

    def get(self, request, uidb64, token):
        user, valid = self._get_user(uidb64, token)
        if not valid:
            return render(request, self.template_name, {"invalid": True})
        return render(request, self.template_name, {"validlink": True, "uidb64": uidb64, "token": token})

    def post(self, request, uidb64, token):
        user, valid = self._get_user(uidb64, token)
        if not valid:
            return render(request, self.template_name, {"invalid": True})
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password updated. You can now log in.")
            return redirect("login")
        return render(request, self.template_name, {
            "validlink": True, "form": form,
            "uidb64": uidb64, "token": token,
        })
