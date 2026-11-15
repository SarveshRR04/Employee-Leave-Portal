
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import User


def dashboard_url_name(user):
    return "admin_dashboard" if user.is_admin else "employee_dashboard"


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, "You do not have permission to open that page.")
                return redirect(dashboard_url_name(request.user))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


employee_required = role_required(User.ROLE_EMPLOYEE)
admin_required = role_required(User.ROLE_ADMIN)
