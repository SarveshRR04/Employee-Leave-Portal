
from django.contrib import messages
from django.shortcuts import redirect, render

from .decorators import employee_required
from .forms import LeaveRequestForm
from .models import LeaveRequest, get_balances


@employee_required
def employee_dashboard(request):
    """Balance cards + the 5 most recent requests."""
    return render(request, "employee/dashboard.html", {
        "balances": get_balances(request.user),
        "recent_leaves": request.user.leave_requests.select_related("leave_type")[:5],
    })


@employee_required
def apply_leave(request):
    balances = get_balances(request.user)
    form = LeaveRequestForm(request.POST or None, employee=request.user)

    if request.method == "POST" and form.is_valid():
        leave = form.save(commit=False)
        leave.employee = request.user  
        leave.save()                    
        messages.success(request, "Leave request submitted. It is now waiting for admin approval.")
        return redirect("my_leaves")

    return render(request, "employee/apply_leave.html", {"form": form, "balances": balances})


@employee_required
def my_leaves(request):
    status = request.GET.get("status", "")
    leaves = request.user.leave_requests.select_related("leave_type", "reviewed_by")
    if status in dict(LeaveRequest.STATUS_CHOICES):
        leaves = leaves.filter(status=status)

    return render(request, "employee/my_leaves.html", {
        "leaves": leaves,
        "status": status,
        "status_choices": LeaveRequest.STATUS_CHOICES,
    })
