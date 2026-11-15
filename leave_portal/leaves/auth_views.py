
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .decorators import dashboard_url_name
from .forms import LoginForm
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_name(request.user))
    return render(request, "home.html")


def login_view(request, role):
   
    if request.user.is_authenticated:
        return redirect(dashboard_url_name(request.user))

    expected_role = User.ROLE_ADMIN if role == "admin" else User.ROLE_EMPLOYEE
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            form.add_error(None, "Invalid email or password.")
        elif user.role != expected_role:
            form.add_error(None, f"This account cannot use the {role} login.")
        else:
            login(request, user)  # creates the session
            messages.success(request, f"Welcome, {user.first_name or user.email}!")
            return redirect(dashboard_url_name(user))

    return render(request, "login.html", {"form": form, "role": role})


@require_POST  
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")
