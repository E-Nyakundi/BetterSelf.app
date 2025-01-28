from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from .forms import CreateUserForm, LoginForm  # Ensure you have these forms defined

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
