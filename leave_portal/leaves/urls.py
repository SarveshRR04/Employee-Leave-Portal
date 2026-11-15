from django.urls import path

from . import admin_views, auth_views, employee_views

urlpatterns = [
    
    path("", auth_views.home, name="home"),
    path("login/employee/", auth_views.login_view, {"role": "employee"}, name="employee_login"),
    path("login/admin/", auth_views.login_view, {"role": "admin"}, name="admin_login"),
    path("logout/", auth_views.logout_view, name="logout"),


    path("employee/dashboard/", employee_views.employee_dashboard, name="employee_dashboard"),
    path("employee/apply/", employee_views.apply_leave, name="apply_leave"),
    path("employee/my-leaves/", employee_views.my_leaves, name="my_leaves"),

    path("admin-panel/dashboard/", admin_views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/leaves/", admin_views.leave_requests, name="leave_requests"),
    path("admin-panel/leaves/<int:pk>/approve/", admin_views.approve_leave, name="approve_leave"),
    path("admin-panel/leaves/<int:pk>/reject/", admin_views.reject_leave, name="reject_leave"),
    path("admin-panel/employees/", admin_views.employee_list, name="employee_list"),
    path("admin-panel/employees/<int:pk>/", admin_views.employee_detail, name="employee_detail"),
    path("admin-panel/reports/", admin_views.reports, name="reports"),
    path("admin-panel/api/pending-count/", admin_views.pending_count_api, name="pending_count_api"),
]
