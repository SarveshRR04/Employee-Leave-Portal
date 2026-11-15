
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from leaves.models import LeaveRequest, LeaveType, User, get_balances

ADMIN = {"email": "admin@company.com", "password": "Admin@123",
         "first_name": "Priya", "last_name": "Sharma"}

EMPLOYEE_PASSWORD = "Employee@123"
EMPLOYEES = [
    
    ("arun@company.com", "Arun", "Kumar", "EMP001", "Engineering", "Software Engineer"),
    ("divya@company.com", "Divya", "Raj", "EMP002", "Engineering", "QA Engineer"),
    ("karthik@company.com", "Karthik", "Iyer", "EMP003", "Sales", "Sales Executive"),
    ("meena@company.com", "Meena", "Pillai", "EMP004", "HR", "HR Executive"),
    ("rahul@company.com", "Rahul", "Verma", "EMP005", "Finance", "Accountant"),
    ("sneha@company.com", "Sneha", "Nair", "EMP006", "Marketing", "Marketing Lead"),
]

LEAVE_TYPES = [("Casual Leave", 12), ("Sick Leave", 10), ("Earned Leave", 15)]


class Command(BaseCommand):
    help = "Create demo leave types, users and leave requests"

    def handle(self, *args, **options):
        for name, days in LEAVE_TYPES:
            LeaveType.objects.get_or_create(name=name, defaults={"days_per_year": days})

        admin = User.objects.filter(email=ADMIN["email"]).first()
        if not admin:
            admin = User.objects.create_superuser(**ADMIN)

        employees = []
        for email, first, last, code, dept, desig in EMPLOYEES:
            emp = User.objects.filter(email=email).first()
            if not emp:
                emp = User.objects.create_user(
                    email=email, password=EMPLOYEE_PASSWORD, first_name=first, last_name=last,
                    employee_code=code, department=dept, designation=desig,
                    role=User.ROLE_EMPLOYEE,
                )
            get_balances(emp)
            employees.append(emp)

        if not LeaveRequest.objects.exists():
            self._create_sample_requests(admin, employees)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"  Admin login:    {ADMIN['email']} / {ADMIN['password']}")
        self.stdout.write(f"  Employee login: arun@company.com / {EMPLOYEE_PASSWORD}"
                          " (all employees use this password)")

    def _create_sample_requests(self, admin, emps):
        today = timezone.localdate()
        casual, sick, earned = (LeaveType.objects.get(name=n) for n, _ in LEAVE_TYPES)

        def leave(emp, ltype, start, days, reason):
            return LeaveRequest.objects.create(
                employee=emp, leave_type=ltype, reason=reason,
                start_date=today + timedelta(days=start),
                end_date=today + timedelta(days=start + days - 1),
            )

        
        leave(emps[0], casual, -30, 3, "Family function").approve(admin)
        leave(emps[2], sick, -10, 2, "Fever").approve(admin)
        leave(emps[2], earned, 20, 5, "Vacation trip").approve(admin)
        leave(emps[4], casual, 0, 1, "Personal work").approve(admin)  # on leave today

        
        leave(emps[1], earned, -5, 4, "Travel").reject(admin, "Release week - team needs full strength.")

      
        leave(emps[0], sick, 5, 2, "Doctor appointment")
        leave(emps[1], casual, 10, 3, "Sister's wedding")
        leave(emps[3], earned, 15, 5, "Hometown visit")
