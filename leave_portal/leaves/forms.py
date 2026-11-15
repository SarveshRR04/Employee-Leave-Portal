from django import forms
from django.utils import timezone

from .models import LeaveBalance, LeaveRequest, LeaveType, count_leave_days


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@company.com"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class LeaveRequestForm(forms.ModelForm):
   

    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Reason for leave"}),
        }

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee  
        self.fields["leave_type"].queryset = LeaveType.objects.all()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        leave_type = cleaned.get("leave_type")

        if not (start and end and leave_type):
            return cleaned  

       
        if start < timezone.localdate():
            raise forms.ValidationError("Start date cannot be in the past.")
        if end < start:
            raise forms.ValidationError("End date cannot be before start date.")

        if LeaveRequest.has_overlap(self.employee, start, end):
            raise forms.ValidationError(
                "You already have a pending or approved leave on these dates."
            )

      
        days = count_leave_days(start, end)
        balance = LeaveBalance.objects.filter(employee=self.employee, leave_type=leave_type).first()
        remaining = balance.remaining_days if balance else leave_type.days_per_year
        if days > remaining:
            raise forms.ValidationError(
                f"You asked for {days} days but only have {remaining} {leave_type} days left."
            )

        return cleaned
