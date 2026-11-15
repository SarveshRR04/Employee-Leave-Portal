from .models import LeaveRequest


def pending_count(request):
    if request.user.is_authenticated and request.user.is_admin:
        return {"pending_count": LeaveRequest.objects.filter(status=LeaveRequest.PENDING).count()}
    return {}
