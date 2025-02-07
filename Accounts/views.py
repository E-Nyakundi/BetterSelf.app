from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from .forms import CreateUserForm, LoginForm  # Ensure you have these forms defined
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from django.contrib.auth.forms import AdminPasswordChangeForm  # or use SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileForm
from .models import Profile
@login_required
def set_password(request):
    # Only allow if the user does not have a usable password
    if request.user.has_usable_password():
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AdminPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Update the session so the user is not logged out
            update_session_auth_hash(request, form.user)
            return redirect('dashboard')
    else:
        form = AdminPasswordChangeForm(user=request.user)
    return render(request, 'Accounts/set_password.html', {'form': form})


@login_required
def edit_profile(request):
    # Retrieve or create the profile for the logged-in user.
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={"email": request.user.email, "title": "New User"},
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("dashboard")  # Update to your desired redirect
    else:
        form = ProfileForm(instance=profile)

    return render(request, "Accounts/edit_profile.html", {"form": form})



# Home view function
def HomeView(request):
    template_name = "Accounts/index.html"
    return render(request, template_name)

def DashboardView(request):
    template_name = "Accounts/dashboard.html"

    
    return render(request, template_name)

# Sign-up view class
class SignUpView(View):
    template_name = "Accounts/create_user.html"
    form_class = CreateUserForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {'form': form}
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to welcome page after successful sign up
        return render(request, self.template_name, context)

# Login view class
class LoginView(View):
    template_name = "Accounts/login.html"
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {'form': form}
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to home page after successful login
            else:
                context['error'] = "Invalid username or password"
        return render(request, self.template_name, context)
