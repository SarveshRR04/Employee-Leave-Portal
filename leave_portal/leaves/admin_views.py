
import csv
from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .models import LeaveRequest, LeaveType, User, get_balances



def _get_date(request, name):

    try:
        return parse_date(request.GET.get(name, ""))
    except ValueError:
        return None


def filter_leaves(request, leaves):
    
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    leave_type = request.GET.get("leave_type", "")
    from_date = _get_date(request, "from")
    to_date = _get_date(request, "to")

    if q:
        leaves = leaves.filter(
            Q(employee__first_name__icontains=q)
            | Q(employee__last_name__icontains=q)
            | Q(employee__email__icontains=q)
            | Q(employee__employee_code__icontains=q)
            | Q(employee__department__icontains=q)
        )
    if status in dict(LeaveRequest.STATUS_CHOICES):
        leaves = leaves.filter(status=status)
    if leave_type.isdigit():
        leaves = leaves.filter(leave_type_id=leave_type)
    if from_date:
        leaves = leaves.filter(start_date__gte=from_date)
    if to_date:
        leaves = leaves.filter(start_date__lte=to_date)
    return leaves


def _filter_context(request):
    
    return {
        "q": request.GET.get("q", ""),
        "status": request.GET.get("status", ""),
        "leave_type": request.GET.get("leave_type", ""),
        "from_date": request.GET.get("from", ""),
        "to_date": request.GET.get("to", ""),
        "status_choices": LeaveRequest.STATUS_CHOICES,
        "leave_types": LeaveType.objects.all(),
    }


def _redirect_back(request):
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("leave_requests")



@admin_required
def admin_dashboard(request):
    status_counts = dict(
        LeaveRequest.objects.values_list("status").annotate(n=Count("id"))
    )

    stats = {
        "employees": User.objects.filter(role=User.ROLE_EMPLOYEE).count(),
        "pending": status_counts.get(LeaveRequest.PENDING, 0),
        "approved": status_counts.get(LeaveRequest.APPROVED, 0),
        "rejected": status_counts.get(LeaveRequest.REJECTED, 0),
    }


    chart_data = {
        "status": [stats["pending"], stats["approved"], stats["rejected"]],
    }

    pending_leaves = (
        LeaveRequest.objects.filter(status=LeaveRequest.PENDING)
        .select_related("employee", "leave_type")[:6]
    )

    return render(request, "admin_panel/dashboard.html", {
        "stats": stats,
        "chart_data": chart_data,
        "pending_leaves": pending_leaves,
    })


@admin_required
def pending_count_api(request):
    """Small JSON API. The admin pages call it every 15 seconds to update the badge."""
    count = LeaveRequest.objects.filter(status=LeaveRequest.PENDING).count()
    return JsonResponse({"pending": count})



@admin_required
def leave_requests(request):
    leaves = filter_leaves(
        request, LeaveRequest.objects.select_related("employee", "leave_type", "reviewed_by")
    )
    context = _filter_context(request)
    context["leaves"] = leaves
    return render(request, "admin_panel/leave_requests.html", context)


@admin_required
@require_POST
def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    try:
        leave.approve(request.user)
        messages.success(request, f"Approved {leave.employee}'s {leave.leave_type} leave.")
    except ValidationError as e:
        messages.error(request, e.messages[0])
    return _redirect_back(request)


@admin_required
@require_POST
def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    try:
        leave.reject(request.user, request.POST.get("reason", ""))
        messages.success(request, f"Rejected {leave.employee}'s {leave.leave_type} leave.")
    except ValidationError as e:
        messages.error(request, e.messages[0])
    return _redirect_back(request)


@admin_required
def employee_list(request):
    q = request.GET.get("q", "").strip()
    employees = User.objects.filter(role=User.ROLE_EMPLOYEE).annotate(
        pending=Count("leave_requests", filter=Q(leave_requests__status=LeaveRequest.PENDING)),
        total_requests=Count("leave_requests"),
    ).order_by("first_name")
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
            | Q(email__icontains=q) | Q(employee_code__icontains=q)
            | Q(department__icontains=q)
        )

    rows = [{"employee": e, "balances": get_balances(e)} for e in employees]

    return render(request, "admin_panel/employees.html", {
        "rows": rows,
        "leave_types": LeaveType.objects.all(),
        "q": q,
    })


@admin_required
def employee_detail(request, pk):
    employee = get_object_or_404(User, pk=pk, role=User.ROLE_EMPLOYEE)
    return render(request, "admin_panel/employee_detail.html", {
        "employee": employee,
        "balances": get_balances(employee),
        "leaves": employee.leave_requests.select_related("leave_type"),
    })


@admin_required
def reports(request):
    leaves = filter_leaves(
        request, LeaveRequest.objects.select_related("employee", "leave_type", "reviewed_by")
    )

    if request.GET.get("export") == "csv":
        return _export_csv(leaves)

    summary = {}
    for leave in leaves:
        row = summary.setdefault(leave.employee_id, {
            "employee": leave.employee, "requests": 0,
            "approved_days": 0, "pending": 0, "approved": 0, "rejected": 0,
        })
        row["requests"] += 1
        if leave.status == LeaveRequest.APPROVED:
            row["approved"] += 1
            row["approved_days"] += leave.total_days
        elif leave.status == LeaveRequest.PENDING:
            row["pending"] += 1
        elif leave.status == LeaveRequest.REJECTED:
            row["rejected"] += 1

    rows = list(summary.values())
    totals = {
        "requests": sum(r["requests"] for r in rows),
        "approved": sum(r["approved"] for r in rows),
        "pending": sum(r["pending"] for r in rows),
        "rejected": sum(r["rejected"] for r in rows),
        "approved_days": sum(r["approved_days"] for r in rows),
    }


    query = request.GET.copy()
    query.pop("export", None)

    context = _filter_context(request)
    context.update({"summary": rows, "totals": totals, "query_string": query.urlencode()})
    return render(request, "admin_panel/reports.html", context)


def _export_csv(leaves):
    response = HttpResponse(content_type="text/csv")
    filename = f"leave_report_{date.today():%Y%m%d}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Email", "Department", "Leave Type", "Start", "End",
                     "Days", "Status", "Reason", "Admin Remark", "Applied On"])
    for l in leaves:
        writer.writerow([
            l.employee.get_full_name(), l.employee.email, l.employee.department,
            l.leave_type.name, l.start_date, l.end_date, l.total_days,
            l.get_status_display(), l.reason, l.admin_remark,
            timezone.localtime(l.applied_on).strftime("%Y-%m-%d %H:%M"),
        ])
    return response
