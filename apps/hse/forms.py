# forms.py
from django import forms
from django.utils import timezone
from .models import *

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'activity_field', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام شرکت'}),
            'activity_field': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'حوزه فعالیت'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CompanyDepartmentForm(forms.ModelForm):
    class Meta:
        model = CompanyDepartment
        fields = ['name', 'employee_count', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CompanyMemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['department'].queryset = CompanyDepartment.objects.filter(company=company)
            self.fields['user'].queryset = CustomUser.objects.exclude(
                id__in=company.members.values_list('user_id', flat=True)
            )

    class Meta:
        model = CompanyMember
        fields = ['user', 'department', 'position', 'status']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class InspectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['department'].queryset = CompanyDepartment.objects.filter(company=company)
            self.fields['assigned_to'].queryset = CompanyMember.objects.filter(company=company, is_active=True)

    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'autocomplete': 'off'}),
        initial=timezone.now().date()
    )

    class Meta:
        model = Inspection
        fields = ['title', 'description', 'priority', 'department', 'assigned_to', 'scheduled_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان بازرسی'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }


class IncidentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['department'].queryset = CompanyDepartment.objects.filter(company=company)
            self.fields['reporter'].queryset = CompanyMember.objects.filter(company=company, is_active=True)

    incident_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        initial=timezone.now()
    )

    class Meta:
        model = Incident
        fields = ['title', 'description', 'incident_type', 'severity_level',
                 'department', 'reporter', 'incident_date', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'severity_level': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'reporter': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['department'].queryset = CompanyDepartment.objects.filter(company=company)
            self.fields['assigned_to'].queryset = CompanyMember.objects.filter(company=company, is_active=True)
            self.fields['related_inspection'].queryset = Inspection.objects.filter(company=company)
            self.fields['related_incident'].queryset = Incident.objects.filter(company=company)

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'autocomplete': 'off'})
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'department', 'assigned_to',
                 'due_date', 'related_inspection', 'related_incident']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'related_inspection': forms.Select(attrs={'class': 'form-select'}),
            'related_incident': forms.Select(attrs={'class': 'form-select'}),
        }


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['invited_user', 'department', 'position', 'message']
        widgets = {
            'invited_user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class HSEReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['prepared_by'].queryset = CompanyMember.objects.filter(company=company, is_active=True)
            self.fields['approved_by'].queryset = CompanyMember.objects.filter(company=company, is_active=True)

    period_start = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'text'})
    )

    period_end = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'text'})
    )

    class Meta:
        model = HSEReport
        fields = ['title', 'report_type', 'period_start', 'period_end',
                 'recommendations', 'conclusions', 'prepared_by', 'approved_by']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conclusions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prepared_by': forms.Select(attrs={'class': 'form-select'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
        }




# forms.py
from django import forms
from .models import Invitation

class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['invited_user', 'department', 'position', 'message']
        widgets = {
            'invited_user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



from django import forms
from .models import HSEReport, Company, CompanyDepartment, CompanyMember, Inspection, Incident, Task

class HSEReportCreateForm(forms.ModelForm):
    class Meta:
        model = HSEReport
        fields = [
            'title',
            'report_type',
            'period_start',
            'period_end',
            'total_incidents',
            'serious_incidents',
            'minor_incidents',
            'near_misses',
            'total_inspections',
            'completed_inspections',
            'pending_inspections',
            'total_tasks',
            'completed_tasks',
            'overdue_tasks',
            'accident_frequency_rate',
            'accident_severity_rate',
            'safety_performance_index',
            'recommendations',
            'conclusions',
            'prepared_by',
            'approved_by',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان گزارش'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'period_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'period_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_incidents': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'serious_incidents': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'minor_incidents': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'near_misses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'total_inspections': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'completed_inspections': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'pending_inspections': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'total_tasks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'completed_tasks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'overdue_tasks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'accident_frequency_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'accident_severity_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'safety_performance_index': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توصیه‌های گزارش'
            }),
            'conclusions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'نتیجه‌گیری گزارش'
            }),
            'prepared_by': forms.Select(attrs={
                'class': 'form-select'
            }),
            'approved_by': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'عنوان گزارش',
            'report_type': 'نوع گزارش',
            'period_start': 'تاریخ شروع دوره',
            'period_end': 'تاریخ پایان دوره',
            'total_incidents': 'تعداد کل حوادث',
            'serious_incidents': 'حوادث شدید',
            'minor_incidents': 'حوادث جزئی',
            'near_misses': 'شبه حوادث',
            'total_inspections': 'تعداد بازرسی‌ها',
            'completed_inspections': 'بازرسی‌های تکمیل شده',
            'pending_inspections': 'بازرسی‌های در انتظار',
            'total_tasks': 'تعداد وظایف',
            'completed_tasks': 'وظایف تکمیل شده',
            'overdue_tasks': 'وظایف معوقه',
            'accident_frequency_rate': 'نرخ فراوانی حوادث',
            'accident_severity_rate': 'نرخ شدت حوادث',
            'safety_performance_index': 'شاخص عملکرد ایمنی',
            'recommendations': 'توصیه‌ها',
            'conclusions': 'نتیجه‌گیری',
            'prepared_by': 'تهیه کننده',
            'approved_by': 'تایید کننده',
        }




# apps/hse/forms.py - بخش آموزش‌ها
class TrainingCreateForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = [
            'title',
            'description',
            'training_type',
            'level',
            'department',
            'video',
            'attachment',
            'duration_minutes',
            'scheduled_date',
            'instructor',
            'participants',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان آموزش'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'توضیحات آموزش'
            }),
            'training_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'instructor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'عنوان آموزش',
            'description': 'توضیحات',
            'training_type': 'نوع آموزش',
            'level': 'سطح آموزش',
            'department': 'بخش',
            'video': 'فیلم آموزش',
            'attachment': 'ضمیمه',
            'duration_minutes': 'مدت زمان (دقیقه)',
            'scheduled_date': 'تاریخ و زمان برگزاری',
            'instructor': 'مدرس',
            'participants': 'شرکت‌کنندگان',
        }


class TrainingUpdateForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = [
            'title',
            'description',
            'training_type',
            'level',
            'status',
            'department',
            'video',
            'attachment',
            'duration_minutes',
            'scheduled_date',
            'completion_date',
            'instructor',
            'participants',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان آموزش'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'توضیحات آموزش'
            }),
            'training_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'completion_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'instructor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'عنوان آموزش',
            'description': 'توضیحات',
            'training_type': 'نوع آموزش',
            'level': 'سطح آموزش',
            'status': 'وضعیت',
            'department': 'بخش',
            'video': 'فیلم آموزش',
            'attachment': 'ضمیمه',
            'duration_minutes': 'مدت زمان (دقیقه)',
            'scheduled_date': 'تاریخ و زمان برگزاری',
            'completion_date': 'تاریخ تکمیل',
            'instructor': 'مدرس',
            'participants': 'شرکت‌کنندگان',
        }