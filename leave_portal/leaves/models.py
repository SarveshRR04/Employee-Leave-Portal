
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone



class UserManager(BaseUserManager):
    

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)  # stores a hash, never the plain password
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.ROLE_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_ADMIN = "ADMIN"
    ROLE_EMPLOYEE = "EMPLOYEE"
    ROLE_CHOICES = [(ROLE_ADMIN, "Admin"), (ROLE_EMPLOYEE, "Employee")]

    username = None  # we log in with email instead
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    employee_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_employee(self):
        return self.role == self.ROLE_EMPLOYEE

    def __str__(self):
        return self.get_full_name() or self.email


class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    days_per_year = models.PositiveIntegerField(default=12)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    total_days = models.PositiveIntegerField()
    used_days = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("employee", "leave_type")  # one row per employee per type
        ordering = ["leave_type__name"]

    @property
    def remaining_days(self):
        return self.total_days - self.used_days

    def __str__(self):
        return f"{self.employee} - {self.leave_type}: {self.remaining_days} left"


def get_balances(employee):
    
    for leave_type in LeaveType.objects.all():
        LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            defaults={"total_days": leave_type.days_per_year},
        )
    return LeaveBalance.objects.filter(employee=employee).select_related("leave_type")



def count_leave_days(start_date, end_date):
    
    return (end_date - start_date).days + 1


class LeaveRequest(models.Model):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    STATUS_CHOICES = [(PENDING, "Pending"), (APPROVED, "Approved"), (REJECTED, "Rejected")]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    admin_remark = models.TextField(blank=True)  # reason given when rejecting
    applied_on = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_leaves"
    )

    class Meta:
        ordering = ["-applied_on"]  # newest first

    def __str__(self):
        return f"{self.employee} | {self.leave_type} | {self.start_date} to {self.end_date}"

    @property
    def total_days(self):
        return count_leave_days(self.start_date, self.end_date)



    @staticmethod
    def has_overlap(employee, start_date, end_date, exclude_id=None):
       
        qs = LeaveRequest.objects.filter(
            employee=employee,
            status__in=[LeaveRequest.PENDING, LeaveRequest.APPROVED],
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def approve(self, admin_user):
       
        with transaction.atomic():
            leave = LeaveRequest.objects.select_for_update().get(pk=self.pk)
            if leave.status != LeaveRequest.PENDING:
                raise ValidationError("Only pending requests can be approved.")

            get_balances(leave.employee)  
            balance = LeaveBalance.objects.select_for_update().get(
                employee=leave.employee, leave_type=leave.leave_type
            )
            if leave.total_days > balance.remaining_days:
                raise ValidationError(
                    f"Not enough {leave.leave_type} balance "
                    f"({balance.remaining_days} days left, {leave.total_days} requested)."
                )

            balance.used_days += leave.total_days
            balance.save()

            leave.status = LeaveRequest.APPROVED
            leave.reviewed_by = admin_user
            leave.reviewed_on = timezone.now()
            leave.save()
        self.refresh_from_db()

    def reject(self, admin_user, reason):

        if self.status != LeaveRequest.PENDING:
            raise ValidationError("Only pending requests can be rejected.")
        if not reason or not reason.strip():
            raise ValidationError("Please give a reason for rejecting.")
        self.status = LeaveRequest.REJECTED
        self.admin_remark = reason.strip()
        self.reviewed_by = admin_user
        self.reviewed_on = timezone.now()
        self.save()
