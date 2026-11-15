

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import LeaveBalance, LeaveRequest, LeaveType, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "role", "employee_code", "department"]
    list_filter = ["role", "department", "is_active"]
    search_fields = ["email", "first_name", "last_name", "employee_code"]

    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ["first_name", "last_name", "employee_code",
                                      "department", "designation"]}),
        ("Role & permissions", {"fields": ["role", "is_active", "is_staff", "is_superuser"]}),
    ]
    add_fieldsets = [
        (None, {
            "classes": ["wide"],
            "fields": ["email", "first_name", "last_name", "role", "employee_code",
                       "department", "designation", "password1", "password2"],
        }),
    ]


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "days_per_year"]


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "total_days", "used_days", "remaining_days"]
    list_filter = ["leave_type"]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "status", "applied_on"]
    list_filter = ["status", "leave_type"]
    search_fields = ["employee__email", "employee__first_name", "employee__last_name"]
