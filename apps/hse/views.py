# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
import json
from datetime import datetime, timedelta
from apps.user.model.user import CustomUser
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from .models import (
    Company, CompanyDepartment, CompanyMember, Inspection,
    Incident, Task, Invitation, Notification, HSEReport
)
from .forms import (
    CompanyForm, CompanyDepartmentForm, CompanyMemberForm,
    InspectionForm, IncidentForm, TaskForm, InvitationForm,
    HSEReportForm
)

from .decorators import login_required_company_member,require_company_access,company_access,company_member_access

# ==================== Company Views ====================

@login_required_company_member
def company_list(request):
    """لیست شرکت‌های کاربر (مالک + عضو)"""

    # استفاده از Q objects برای پیدا کردن همه شرکت‌های مرتبط
    companies = Company.objects.filter(
        Q(user=request.user) |  # یا مالک باشد
        Q(members__user=request.user, members__is_active=True)  # یا عضو فعال باشد
    ).distinct().order_by('-created_at')

    # جمع‌آوری اطلاعات نقش
    company_info = []
    for company in companies:
        if company.user == request.user:
            role = 'مالک'
            is_owner = True
        else:
            try:
                member = CompanyMember.objects.get(
                    company=company,
                    user=request.user,
                    is_active=True
                )
                role = member.get_position_display()
                is_owner = False
            except CompanyMember.DoesNotExist:
                role = 'عضو'
                is_owner = False

        company_info.append({
            'company': company,
            'role': role,
            'is_owner': is_owner,
        })

    stats = {
        'total': companies.count(),
        'active': companies.filter(is_active=True).count(),
        'departments': CompanyDepartment.objects.filter(company__in=companies).count(),
        'members': CompanyMember.objects.filter(company__in=companies, is_active=True).count(),
    }

    return render(request, 'hse/company/list.html', {
        'company_info': company_info,
        'stats': stats,
        'page_title': 'شرکت‌های من'
    })


@login_required_company_member
@require_http_methods(["DELETE"])
def company_delete(request, pk):
    """حذف شرکت"""
    try:
        # پیدا کردن شرکت یا ارور 404
        company = get_object_or_404(Company, id=pk)

        # بررسی دسترسی کاربر - فقط کاربر ایجادکننده می‌تواند حذف کند
        if company.user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'شما مجوز حذف این شرکت را ندارید'
            }, status=403)

        # ذخیره نام شرکت برای پیام موفقیت
        company_name = company.name

        # حذف شرکت
        company.delete()

        return JsonResponse({
            'success': True,
            'message': f'شرکت "{company_name}" با موفقیت حذف شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required_company_member

def company_detail(request, company_id):
    """جزئیات شرکت"""
    company = get_object_or_404(Company, id=company_id)

    # آمارهای شرکت
    departments = company.departments.filter(is_active=True)
    members = company.members.filter(is_active=True)

    # آمار بازرسی‌ها
    inspections = company.inspections.all()
    inspection_stats = {
        'total': inspections.count(),
        'completed': inspections.filter(status='COMPLETED').count(),
        'in_progress': inspections.filter(status='IN_PROGRESS').count(),
    }

    # آمار حوادث
    incidents = company.incidents.all()
    incident_stats = {
        'total': incidents.count(),
        'resolved': incidents.filter(status='RESOLVED').count(),
        'severe': incidents.filter(severity_level='SEVERE').count(),
    }

    # آمار وظایف
    tasks = company.tasks.all()
    task_stats = {
        'total': tasks.count(),
        'completed': tasks.filter(status='COMPLETED').count(),
        'overdue': tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['PENDING', 'IN_PROGRESS']
        ).count(),
    }

    context = {
        'company': company,
        'departments': departments,
        'members': members,
        'inspection_stats': inspection_stats,
        'incident_stats': incident_stats,
        'task_stats': task_stats,
        'page_title': f'شرکت {company.name}'
    }
    return render(request, 'hse/company/detail.html', context)

@login_required_company_member
def company_create(request):
    """ایجاد شرکت جدید"""
    # آمار شرکت‌های کاربر
    user_companies = Company.objects.filter(user=request.user)

    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect': reverse('hse:company_detail', args=[company.id])
                })

            messages.success(request, 'شرکت با موفقیت ایجاد شد.')
            return redirect('hse:company_detail', company_id=company.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=400)

    else:
        form = CompanyForm()

    context = {
        'form': form,
        'user_companies_count': user_companies.count(),
        'active_companies_count': user_companies.filter(is_active=True).count(),
        'page_title': 'ایجاد شرکت جدید'
    }
    return render(request, 'hse/company/create.html', context)



@login_required_company_member
def company_edit(request, company_id):
    """ویرایش شرکت"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'شرکت با موفقیت ویرایش شد.')
            return redirect('hse:company_detail', company_id=company.id)
    else:
        form = CompanyForm(instance=company)

    context = {
        'form': form,
        'company': company,
        'page_title': f'ویرایش شرکت {company.name}'
    }
    return render(request, 'hse/company/edit.html', context)


@login_required_company_member
@require_POST
def company_toggle_active(request, company_id):
    """تغییر وضعیت فعال/غیرفعال شرکت"""
    company = get_object_or_404(Company, id=company_id)
    company.is_active = not company.is_active
    company.save()

    return JsonResponse({
        'success': True,
        'is_active': company.is_active
    })


# ==================== Department Views ====================
@login_required_company_member
def department_list(request, company_id):
    """لیست بخش‌های شرکت"""
    company = get_object_or_404(Company, id=company_id)
    departments = company.departments.all().order_by('name')

    context = {
        'company': company,
        'departments': departments,
        'page_title': f'بخش‌های شرکت {company.name}'
    }
    return render(request, 'hse/department/list.html', context)

@login_required_company_member
def department_create(request, company_id):
    """ایجاد بخش جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        # دریافت داده‌ها از فرم
        name = request.POST.get('name', '').strip()
        employee_count = request.POST.get('employee_count', '1')
        manager_id = request.POST.get('manager', '')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'

        # اعتبارسنجی
        errors = {}

        # اعتبارسنجی نام
        if not name:
            errors['name'] = 'نام بخش الزامی است'
        elif len(name) < 2:
            errors['name'] = 'نام بخش باید حداقل ۲ حرف باشد'

        # اعتبارسنجی تعداد کارکنان
        try:
            employee_count_int = int(employee_count)
            if employee_count_int < 1:
                errors['employee_count'] = 'تعداد کارکنان باید حداقل ۱ باشد'
        except ValueError:
            errors['employee_count'] = 'لطفا عدد معتبر وارد کنید'

        # اگر خطایی وجود دارد
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
            else:
                context = {
                    'company': company,
                    'errors': errors,
                    'form_data': request.POST
                }
                return render(request, 'hse/department/create.html', context)

        # ایجاد بخش
        try:
            department = CompanyDepartment(
                company=company,
                name=name,
                employee_count=employee_count_int,
                description=description,
                is_active=is_active
            )

            # اگر مدیر انتخاب شده باشد
            if manager_id:
                try:
                    # ابتدا از CustomUser پیدا کنید
                    manager_user = CustomUser.objects.get(id=manager_id)
                    # سپس از CompanyMember مربوطه پیدا کنید
                    company_member = CompanyMember.objects.filter(
                        company=company,
                        user=manager_user
                    ).first()

                    if company_member:
                        department.manager = manager_user  # نه CompanyMember
                    else:
                        errors['manager'] = 'کاربر انتخاب شده عضو این شرکت نیست'
                except CustomUser.DoesNotExist:
                    errors['manager'] = 'کاربر انتخاب شده وجود ندارد'

            # ذخیره بخش
            department.save()

            # پاسخ AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'بخش با موفقیت ایجاد شد',
                    'redirect': reverse('hse:department_list', args=[company.id])
                })

            # پاسخ معمول
            messages.success(request, 'بخش با موفقیت ایجاد شد.')
            return redirect('hse:department_list', company_id=company.id)

        except Exception as e:
            error_msg = str(e)
            if 'unique' in error_msg.lower():
                errors['name'] = 'بخش با این نام قبلاً ثبت شده است'
            else:
                errors['__all__'] = f'خطا در ایجاد بخش: {error_msg}'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
            else:
                context = {
                    'company': company,
                    'errors': errors,
                    'form_data': request.POST
                }
                return render(request, 'hse/department/create.html', context)

    # GET request
    context = {
        'company': company,
        'page_title': 'ایجاد بخش جدید'
    }
    return render(request, 'hse/department/create.html', context)


@login_required_company_member
def department_edit(request, company_id, department_id):
    """ویرایش بخش"""
    company = get_object_or_404(Company, id=company_id)
    department = get_object_or_404(CompanyDepartment, id=department_id, company=company)

    if request.method == 'POST':
        form = CompanyDepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'بخش با موفقیت ویرایش شد.')
            return redirect('hse:department_list', company_id=company.id)
    else:
        form = CompanyDepartmentForm(instance=department)

    context = {
        'form': form,
        'company': company,
        'department': department,
        'page_title': f'ویرایش بخش {department.name}'
    }
    return render(request, 'hse/department/edit.html', context)


# ==================== Company Member Views ====================
@login_required_company_member
def member_list(request, company_id):
    """لیست اعضای شرکت"""
    company = get_object_or_404(Company, id=company_id)
    members = company.members.all().select_related('user', 'department').order_by('-join_date')

    # فیلترها
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')

    if status_filter:
        members = members.filter(status=status_filter)

    if department_filter:
        members = members.filter(department_id=department_filter)

    departments = company.departments.all()

    context = {
        'company': company,
        'members': members,
        'departments': departments,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'page_title': f'اعضای شرکت {company.name}'
    }
    return render(request, 'hse/company/member_list.html', context)

# views.py - به‌روزرسانی member_add
@login_required_company_member
def member_add(request, company_id):
    """افزودن عضو به شرکت"""
    company = get_object_or_404(Company, id=company_id)

    # کاربران موجود که عضو این شرکت نیستند
    existing_member_ids = company.members.values_list('user_id', flat=True)
    available_users = CustomUser.objects.exclude(id__in=existing_member_ids)

    if request.method == 'POST':
        form = CompanyMemberForm(request.POST, company=company)
        if form.is_valid():
            member = form.save(commit=False)
            member.company = company
            member.save()

            messages.success(request, 'عضو با موفقیت به شرکت اضافه شد.')
            return redirect('hse:member_list', company_id=company.id)
    else:
        form = CompanyMemberForm(company=company)

    context = {
        'form': form,
        'company': company,
        'available_users': available_users,
        'page_title': 'افزودن عضو جدید'
    }
    return render(request, 'hse/company/member_add.html', context)


# ==================== Inspection Views ====================

# apps/hse/views.py
@login_required_company_member
def inspection_list(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    inspections = Inspection.objects.filter(company=company)

    # فیلترها
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    department_filter = request.GET.get('department')

    if status_filter:
        inspections = inspections.filter(status=status_filter)
    if priority_filter:
        inspections = inspections.filter(priority=priority_filter)
    if department_filter:
        inspections = inspections.filter(department_id=department_filter)

    departments = CompanyDepartment.objects.filter(company=company)

    context = {
        'company': company,
        'inspections': inspections,
        'departments': departments,
        'inspection_status_choices': Inspection.STATUS_CHOICES,  # این خط اضافه شود
        'inspection_priority_choices': Inspection.PRIORITY_CHOICES,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'department_filter': department_filter,
    }
    return render(request, 'hse/inspection/list.html', context)

@login_required_company_member
def inspection_detail(request, company_id, inspection_id):
    company = get_object_or_404(Company, id=company_id)
    inspection = get_object_or_404(Inspection, id=inspection_id, company=company)

    # فرم برای تغییر وضعیت
    if request.method == 'POST' and 'status' in request.POST:
        new_status = request.POST.get('status')
        if new_status in [Inspection.DRAFT, Inspection.IN_PROGRESS, Inspection.COMPLETED]:
            inspection.status = new_status
            if new_status == Inspection.COMPLETED:
                inspection.completed_date = timezone.now().date()
            inspection.save()
            messages.success(request, 'وضعیت بازرسی با موفقیت به‌روز شد.')
            return redirect('hse:inspection_detail', company_id=company.id, inspection_id=inspection.id)

    context = {
        'company': company,
        'inspection': inspection,
        'inspection_status_choices': Inspection.STATUS_CHOICES,  # این خط اضافه شود
    }
    return render(request, 'hse/inspection/detail.html', context)


@login_required_company_member
def inspection_create(request, company_id):
    """ایجاد بازرسی جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = InspectionForm(request.POST, company=company)
        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.company = company
            inspection.created_by = request.user
            inspection.save()
            messages.success(request, 'بازرسی با موفقیت ایجاد شد.')
            return redirect('hse:inspection_detail', company_id=company.id, inspection_id=inspection.id)
    else:
        form = InspectionForm(company=company)

    context = {
        'form': form,
        'company': company,
        'page_title': 'ایجاد بازرسی جدید'
    }
    return render(request, 'hse/inspection/create.html', context)


@login_required_company_member
@require_POST
def inspection_update_status(request, company_id, inspection_id):
    """بروزرسانی وضعیت بازرسی"""
    company = get_object_or_404(Company, id=company_id)
    inspection = get_object_or_404(Inspection, id=inspection_id, company=company)

    new_status = request.POST.get('status')
    if new_status in dict(Inspection.Status.choices):
        inspection.status = new_status

        if new_status == 'COMPLETED':
            inspection.completed_date = timezone.now().date()

        inspection.save()
        messages.success(request, 'وضعیت بازرسی بروزرسانی شد.')

    return redirect('inspection_detail', company_id=company.id, inspection_id=inspection.id)


# ==================== Incident Views ====================

@login_required_company_member
def incident_list(request, company_id):
    """لیست حوادث"""
    company = get_object_or_404(Company, id=company_id)
    incidents = company.incidents.all().select_related(
        'department', 'reporter__user'
    ).order_by('-incident_date')

    # فیلترها
    status_filter = request.GET.get('status', '')
    severity_filter = request.GET.get('severity', '')
    type_filter = request.GET.get('type', '')

    if status_filter:
        incidents = incidents.filter(status=status_filter)

    if severity_filter:
        incidents = incidents.filter(severity_level=severity_filter)

    if type_filter:
        incidents = incidents.filter(incident_type=type_filter)

    # آمارها
    stats = {
        'total': incidents.count(),
        'resolved': incidents.filter(status='RESOLVED').count(),
        'severe': incidents.filter(severity_level='SEVERE').count(),
        'this_month': incidents.filter(
            incident_date__month=timezone.now().month,
            incident_date__year=timezone.now().year
        ).count(),
    }

    context = {
        'company': company,
        'incidents': incidents,
        'stats': stats,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'type_filter': type_filter,
        'page_title': f'حوادث شرکت {company.name}'
    }
    return render(request, 'hse/incident/list.html', context)

# apps/hse/views.py
@login_required_company_member
def incident_detail(request, company_id, incident_id):
    company = get_object_or_404(Company, id=company_id)
    incident = get_object_or_404(Incident, id=incident_id, company=company)

    # تغییر وضعیت
    if request.method == 'POST' and 'status' in request.POST:
        new_status = request.POST.get('status')
        # بررسی معتبر بودن وضعیت
        valid_statuses = [choice[0] for choice in Incident.STATUS_CHOICES]
        if new_status in valid_statuses:
            incident.status = new_status
            incident.save()
            messages.success(request, 'وضعیت حادثه با موفقیت به‌روز شد.')
            return redirect('hse:incident_detail', company_id=company.id, incident_id=incident.id)

    context = {
        'company': company,
        'incident': incident,
        'status_choices': Incident.STATUS_CHOICES,
    }
    return render(request, 'hse/incident/detail.html', context)


@login_required_company_member
def incident_create(request, company_id):
    """گزارش حادثه جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = IncidentForm(request.POST, company=company)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.company = company

            # اگر کاربر عضو شرکت است، به عنوان گزارش‌دهنده ثبت می‌شود
            try:
                member = CompanyMember.objects.get(company=company, user=request.user)
                incident.reporter = member
            except CompanyMember.DoesNotExist:
                pass

            incident.save()
            messages.success(request, 'حادثه با موفقیت گزارش شد.')
            return redirect('hse:incident_detail', company_id=company.id, incident_id=incident.id)
    else:
        form = IncidentForm(company=company)

    context = {
        'form': form,
        'company': company,
        'page_title': 'گزارش حادثه جدید'
    }
    return render(request, 'hse/incident/create.html', context)


# ==================== Task Views ====================
@login_required_company_member
def task_list(request, company_id):
    """لیست وظایف"""
    company = get_object_or_404(Company, id=company_id)
    tasks = company.tasks.all().select_related(
        'department', 'assigned_to__user', 'created_by',
        'related_inspection', 'related_incident'
    ).order_by('-created_at')

    # فیلترها
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assigned_to_filter = request.GET.get('assigned_to', '')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if assigned_to_filter:
        tasks = tasks.filter(assigned_to_id=assigned_to_filter)

    # وظایف شخصی کاربر
    if request.GET.get('my_tasks'):
        try:
            member = CompanyMember.objects.get(company=company, user=request.user)
            tasks = tasks.filter(assigned_to=member)
        except CompanyMember.DoesNotExist:
            pass

    members = company.members.filter(is_active=True)

    context = {
        'company': company,
        'tasks': tasks,
        'members': members,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_to_filter': assigned_to_filter,
        'page_title': f'وظایف شرکت {company.name}'
    }
    return render(request, 'hse/task/list.html', context)


# apps/hse/views.py
from datetime import date

@login_required_company_member
def task_detail(request, company_id, task_id):
    company = get_object_or_404(Company, id=company_id)
    task = get_object_or_404(Task, id=task_id, company=company)

    # تغییر وضعیت
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_priority = request.POST.get('priority')

        # بررسی معتبر بودن وضعیت
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        valid_priorities = [choice[0] for choice in Task.PRIORITY_CHOICES]

        if new_status in valid_statuses:
            task.status = new_status
            if new_status == 'COMPLETED' and not task.completed_date:
                task.completed_date = date.today()
            elif new_status != 'COMPLETED':
                task.completed_date = None

        if new_priority in valid_priorities:
            task.priority = new_priority

        task.save()
        messages.success(request, 'تغییرات با موفقیت ذخیره شد.')
        return redirect('hse:task_detail', company_id=company.id, task_id=task.id)

    context = {
        'company': company,
        'task': task,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'today': date.today(),
    }
    return render(request, 'hse/task/detail.html', context)

@login_required_company_member
def task_create(request, company_id):
    """ایجاد وظیفه جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = TaskForm(request.POST, company=company)
        if form.is_valid():
            task = form.save(commit=False)
            task.company = company
            task.created_by = request.user
            task.save()
            messages.success(request, 'وظیفه با موفقیت ایجاد شد.')
            return redirect('hse:task_detail', company_id=company.id, task_id=task.id)
    else:
        form = TaskForm(company=company)

    context = {
        'form': form,
        'company': company,
        'page_title': 'ایجاد وظیفه جدید'
    }
    return render(request, 'hse/task/create.html', context)


@login_required_company_member
@require_POST
def task_update_status(request, company_id, task_id):
    """بروزرسانی وضعیت وظیفه"""
    company = get_object_or_404(Company, id=company_id)
    task = get_object_or_404(Task, id=task_id, company=company)

    new_status = request.POST.get('status')
    if new_status in dict(Task.Status.choices):
        task.status = new_status

        if new_status == 'COMPLETED':
            task.completed_date = timezone.now().date()

        task.save()
        messages.success(request, 'وضعیت وظیفه بروزرسانی شد.')

    return redirect('task_detail', company_id=company.id, task_id=task.id)


# ======from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import re
import uuid
from datetime import timedelta

from .models import (
    Company, CompanyDepartment, CompanyMember,
    Invitation, Notification, CustomUser
)

# ==================== Invitation Views ====================

@login_required_company_member
def invitation_create(request, company_id):
    """ایجاد دعوت‌نامه جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        mobile = request.POST.get('mobile_number', '').strip()
        position = request.POST.get('position', '')
        department_id = request.POST.get('department') or None
        message = request.POST.get('message', '')

        # اعتبارسنجی
        errors = []
        if not mobile:
            errors.append('شماره موبایل الزامی است')
        elif not re.match(r'^09\d{9}$', mobile):
            errors.append('شماره موبایل باید با 09 شروع شده و 11 رقم باشد')
        if not position:
            errors.append('انتخاب سمت الزامی است')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # پیدا کردن کاربر با این شماره
                user = None
                try:
                    user = CustomUser.objects.get(mobileNumber=mobile)
                except CustomUser.DoesNotExist:
                    pass  # کاربر وجود ندارد، مشکلی نیست

                # بررسی دعوت‌نامه pending برای این کاربر/شماره
                if user:
                    existing = Invitation.objects.filter(
                        company=company,
                        invited_user=user,
                        status='PENDING'
                    ).first()
                else:
                    existing = Invitation.objects.filter(
                        company=company,
                        invited_mobile=mobile,
                        status='PENDING'
                    ).first()

                if existing:
                    messages.warning(request, 'دعوت‌نامه قبلی برای این شماره هنوز در انتظار است')
                    return redirect('hse:invitation_list', company_id=company.id)

                # اگر کاربر وجود دارد و قبلاً عضو شده
                if user and CompanyMember.objects.filter(company=company, user=user).exists():
                    messages.warning(request, 'این کاربر قبلاً عضو شرکت است')
                    return redirect('hse:invitation_list', company_id=company.id)

                # ایجاد دعوت‌نامه
                invitation = Invitation(
                    company=company,
                    invited_user=user,
                    invited_mobile=mobile if not user else None,
                    inviter=request.user,
                    department_id=department_id,
                    position=position,
                    message=message,
                    token=str(uuid.uuid4()),
                    expires_at=timezone.now() + timezone.timedelta(days=7),
                    status='PENDING'
                )
                invitation.save()

                # ایجاد اعلان اگر کاربر وجود دارد
                if user:
                    Notification.objects.create(
                        user=user,
                        title=f'📨 دعوت به شرکت {company.name}',
                        message=f'شما برای عضویت در شرکت {company.name} دعوت شده‌اید. سمت پیشنهادی: {invitation.get_position_display()}',
                        notification_type='INVITATION',
                        related_object_id=invitation.id,
                        related_object_type='invitation'
                    )
                    messages.success(request, f'دعوت برای {user.get_full_name() or mobile} ارسال شد')
                else:
                    messages.success(request, f'دعوت برای شماره {mobile} ذخیره شد')

                return redirect('hse:invitation_list', company_id=company.id)

            except Exception as e:
                messages.error(request, f'خطا: {str(e)}')
                print(f"Error creating invitation: {e}")

    # نمایش فرم
    context = {
        'company': company,
        'page_title': 'دعوت عضو جدید'
    }
    return render(request, 'hse/invitation/create.html', context)


@login_required_company_member
def invitation_list(request, company_id):
    """لیست دعوت‌نامه‌های ارسالی"""
    company = get_object_or_404(Company, id=company_id)
    invitations = company.invitations.all().select_related(
        'invited_user', 'inviter', 'department'
    ).order_by('-created_at')

    # در view invitation_list
    context = {
        'company': company,
        'invitations': invitations,
        'page_title': f'دعوت‌نامه‌های شرکت {company.name}',
        'stats': {
            'total': invitations.count(),
            'pending': invitations.filter(status='PENDING').count(),
            'accepted': invitations.filter(status='ACCEPTED').count(),
            'rejected': invitations.filter(status='REJECTED').count(),
            'expired': invitations.filter(status='EXPIRED').count(),
        }
    }
    return render(request, 'hse/invitation/list.html', context)


from django.http import JsonResponse
@login_required_company_member

def invitation_accept(request, token):
    """پذیرش دعوت توسط کاربر"""
    invitation = get_object_or_404(Invitation, token=token)

    # بررسی انقضا
    if invitation.is_expired():
        return JsonResponse({
            'success': False,
            'error': 'این دعوت‌نامه منقضی شده است.'
        }, status=400)

    # بررسی وضعیت
    if invitation.status != 'PENDING':
        return JsonResponse({
            'success': False,
            'error': 'این دعوت‌نامه قبلاً پاسخ داده شده است.'
        }, status=400)

    # بررسی آیا کاربر همان کاربر دعوت شده است
    if invitation.invited_user and invitation.invited_user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'این دعوت‌نامه برای شما نیست.'
        }, status=403)

    # اگر دعوت با شماره موبایل است، بررسی تطابق
    if not invitation.invited_user and invitation.invited_mobile:
        if not hasattr(request.user, 'mobileNumber') or invitation.invited_mobile != request.user.mobileNumber:
            return JsonResponse({
                'success': False,
                'error': 'شماره موبایل شما با دعوت تطابق ندارد.'
            }, status=403)

    try:
        # بررسی آیا کاربر قبلاً عضو شرکت است
        if CompanyMember.objects.filter(company=invitation.company, user=request.user).exists():
            invitation.status = 'ACCEPTED'
            invitation.responded_at = timezone.now()
            invitation.save()

            return JsonResponse({
                'success': True,
                'message': 'شما قبلاً عضو این شرکت هستید.',
                'status': 'ACCEPTED'
            })

        # ایجاد عضو جدید
        member = CompanyMember.objects.create(
            company=invitation.company,
            user=request.user,
            department=invitation.department,
            position=invitation.position,
            status='ACTIVE'
        )

        # بروزرسانی وضعیت دعوت
        invitation.status = 'ACCEPTED'
        invitation.responded_at = timezone.now()
        invitation.save()

        # اعلان به مدیر شرکت
        if invitation.inviter:
            # دریافت نام کاربر به صورت ایمن
            user_display_name = get_user_display_name(request.user)

            Notification.objects.create(
                user=invitation.inviter,
                title=f"{user_display_name} دعوت شما را پذیرفت",
                message=f"{user_display_name} دعوت شما به شرکت {invitation.company.name} را پذیرفت.",
                notification_type='SYSTEM',
                related_object_id=member.id,
                related_object_type='member'
            )

        return JsonResponse({
            'success': True,
            'message': f'شما با موفقیت به شرکت {invitation.company.name} پیوستید.',
            'status': 'ACCEPTED'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطا در پذیرش دعوت: {str(e)}'
        }, status=500)

@require_POST
@login_required_company_member
def invitation_reject(request, token):
    """رد دعوت توسط کاربر"""
    invitation = get_object_or_404(Invitation, token=token)

    if invitation.is_expired():
        return JsonResponse({
            'success': False,
            'error': 'این دعوت‌نامه منقضی شده است.'
        }, status=400)

    if invitation.status != 'PENDING':
        return JsonResponse({
            'success': False,
            'error': 'این دعوت‌نامه قبلاً پاسخ داده شده است.'
        }, status=400)

    # بررسی آیا کاربر همان کاربر دعوت شده است
    if invitation.invited_user and invitation.invited_user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'این دعوت‌نامه برای شما نیست.'
        }, status=403)

    # اگر دعوت با شماره موبایل است، بررسی تطابق
    if not invitation.invited_user and invitation.invited_mobile:
        if not hasattr(request.user, 'mobileNumber') or invitation.invited_mobile != request.user.mobileNumber:
            return JsonResponse({
                'success': False,
                'error': 'شماره موبایل شما با دعوت تطابق ندارد.'
            }, status=403)

    try:
        invitation.status = 'REJECTED'
        invitation.responded_at = timezone.now()
        invitation.save()

        # اعلان به مدیر شرکت
        if invitation.inviter:
            # دریافت نام کاربر به صورت ایمن
            user_display_name = get_user_display_name(request.user)

            Notification.objects.create(
                user=invitation.inviter,
                title=f"{user_display_name} دعوت شما را رد کرد",
                message=f"{user_display_name} دعوت شما به شرکت {invitation.company.name} را رد کرد.",
                notification_type='SYSTEM'
            )

        return JsonResponse({
            'success': True,
            'message': 'دعوت‌نامه رد شد.',
            'status': 'REJECTED'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطا در رد دعوت: {str(e)}'
        }, status=500)

# تابع کمکی برای دریافت نام کاربر
def get_user_display_name(user):
    """دریافت نام نمایشی کاربر به صورت ایمن"""
    if not user.is_authenticated:
        return "کاربر ناشناس"

    # اولویت ۱: get_full_name اگر تابع باشد
    if hasattr(user, 'get_full_name'):
        if callable(user.get_full_name):
            try:
                result = user.get_full_name()
                if result and result.strip():
                    return result.strip()
            except Exception:
                pass
        else:
            # اگر property باشد
            try:
                if user.get_full_name and user.get_full_name.strip():
                    return user.get_full_name.strip()
            except Exception:
                pass

    # اولویت ۲: first_name و last_name
    first_name = getattr(user, 'first_name', '')
    last_name = getattr(user, 'last_name', '')

    if first_name or last_name:
        name_parts = []
        if first_name and first_name.strip():
            name_parts.append(first_name.strip())
        if last_name and last_name.strip():
            name_parts.append(last_name.strip())
        if name_parts:
            return ' '.join(name_parts)

    # اولویت ۳: username
    username = getattr(user, 'username', '')
    if username and username.strip():
        return username.strip()

    # آخرین راه‌حل
    return str(user)

# ==================== Invitation Management Views ====================

@login_required_company_member
def invitation_resend(request, invitation_id):
    """ارسال مجدد دعوت"""
    invitation = get_object_or_404(Invitation, id=invitation_id)

    # بررسی دسترسی - فقط مدیر شرکت می‌تواند ارسال مجدد کند
    if invitation.company.user != request.user:
        messages.error(request, 'شما مجوز ارسال مجدد این دعوت را ندارید')
        return redirect('hse:invitation_list', company_id=invitation.company.id)

    # فقط دعوت‌نامه‌های منقضی یا pending قابل ارسال مجدد هستند
    if invitation.status not in ['PENDING', 'EXPIRED']:
        messages.error(request, 'فقط دعوت‌نامه‌های در انتظار یا منقضی قابل ارسال مجدد هستند')
        return redirect('hse:invitation_list', company_id=invitation.company.id)

    try:
        # ایجاد دعوت جدید با توکن جدید
        new_invitation = Invitation.objects.create(
            company=invitation.company,
            invited_user=invitation.invited_user,
            invited_mobile=invitation.invited_mobile,
            inviter=request.user,
            department=invitation.department,
            position=invitation.position,
            message=invitation.message,
            token=str(uuid.uuid4()),
            expires_at=timezone.now() + timezone.timedelta(days=7),
            status='PENDING'
        )

        # ایجاد اعلان اگر کاربر وجود دارد
        if new_invitation.invited_user:
            Notification.objects.create(
                user=new_invitation.invited_user,
                title=f'📨 دعوت به شرکت {new_invitation.company.name}',
                message=f'شما برای عضویت در شرکت {new_invitation.company.name} دعوت شده‌اید. سمت پیشنهادی: {new_invitation.get_position_display()}',
                notification_type='INVITATION',
                related_object_id=new_invitation.id,
                related_object_type='invitation'
            )
            messages.success(request, f'دعوت مجدد برای {new_invitation.invited_user.get_full_name()} ارسال شد')
        else:
            messages.success(request, f'دعوت مجدد برای شماره {new_invitation.invited_mobile} ارسال شد')

        return redirect('hse:invitation_list', company_id=invitation.company.id)

    except Exception as e:
        messages.error(request, f'خطا در ارسال مجدد دعوت: {str(e)}')
        return redirect('hse:invitation_list', company_id=invitation.company.id)


@login_required_company_member
def invitation_cancel(request, invitation_id):
    """لغو دعوت توسط مدیر شرکت"""
    invitation = get_object_or_404(Invitation, id=invitation_id)

    # بررسی دسترسی
    if invitation.company.user != request.user:
        messages.error(request, 'شما مجوز لغو این دعوت را ندارید')
        return redirect('hse:invitation_list', company_id=invitation.company.id)

    # فقط دعوت‌نامه‌های pending قابل لغو هستند
    if invitation.status != 'PENDING':
        messages.error(request, 'فقط دعوت‌نامه‌های در انتظار قابل لغو هستند')
        return redirect('hse:invitation_list', company_id=invitation.company.id)

    try:
        invitation.status = 'EXPIRED'
        invitation.save()

        messages.success(request, 'دعوت‌نامه با موفقیت لغو شد')
        return redirect('hse:invitation_list', company_id=invitation.company.id)

    except Exception as e:
        messages.error(request, f'خطا در لغو دعوت: {str(e)}')
        return redirect('hse:invitation_list', company_id=invitation.company.id)


# ==================== Notification Views ====================
@login_required_company_member
def notification_list(request):
    """لیست اعلان‌های کاربر با قابلیت پذیرش/رد مستقیم دعوت‌ها"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # محاسبه آمار
    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()

    # برای هر اعلان دعوت، اطلاعات دعوت را نیز بگیریم
    notifications_with_invitation = []
    for notification in notifications:
        notification_data = {
            'notification': notification,
            'invitation': None,
            'can_respond': False
        }

        # اگر اعلان مربوط به دعوت است، اطلاعات دعوت را بگیر
        if notification.notification_type == 'INVITATION' and notification.related_object_id:
            try:
                invitation = Invitation.objects.get(id=notification.related_object_id)
                notification_data['invitation'] = invitation

                # بررسی آیا کاربر می‌تواند دعوت را بپذیرد/رد کند
                if (invitation.status == 'PENDING' and
                    not invitation.is_expired() and
                    ((invitation.invited_user and invitation.invited_user == request.user) or
                     (invitation.invited_mobile and invitation.invited_mobile == request.user.mobileNumber))):
                    notification_data['can_respond'] = True
            except Invitation.DoesNotExist:
                pass

        notifications_with_invitation.append(notification_data)

    # صفحه‌بندی
    paginator = Paginator(notifications_with_invitation, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # علامت‌گذاری اعلان‌های خوانده نشده در این صفحه
    unread_ids = []
    for item in page_obj.object_list:
        if not item['notification'].is_read:
            unread_ids.append(item['notification'].id)

    if unread_ids:
        Notification.objects.filter(id__in=unread_ids).update(is_read=True)
        # به‌روزرسانی تعداد خوانده نشده
        unread_count = max(0, unread_count - len(unread_ids))

    context = {
        'page_obj': page_obj,
        'page_title': 'اعلان‌ها',
        'total_count': total_count,
        'unread_count': unread_count,
    }
    return render(request, 'hse/notification/list.html', context)


@login_required_company_member
@require_GET
def notification_count(request):
    """تعداد اعلان‌های خوانده نشده"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ==================== HSE Report Views ====================
@login_required_company_member
def hse_report_list(request, company_id):
    """لیست گزارشات HSE"""
    company = get_object_or_404(Company, id=company_id)
    reports = company.hse_reports.all().select_related(
        'prepared_by__user', 'approved_by__user'
    ).order_by('-period_end')

    context = {
        'company': company,
        'reports': reports,
        'page_title': f'گزارشات HSE شرکت {company.name}'
    }
    return render(request, 'hse_report/list.html', context)


@login_required_company_member
def hse_report_detail(request, company_id, report_id):
    """جزئیات گزارش HSE"""
    company = get_object_or_404(Company, id=company_id)
    report = get_object_or_404(HSEReport, id=report_id, company=company)

    context = {
        'company': company,
        'report': report,
        'page_title': f'گزارش HSE: {report.title}'
    }
    return render(request, 'hse/hse_report/detail.html', context)


@login_required_company_member
def hse_report_create(request, company_id):
    """ایجاد گزارش HSE جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = HSEReportForm(request.POST, company=company)
        if form.is_valid():
            report = form.save(commit=False)
            report.company = company

            # تنظیم تهیه‌کننده
            try:
                member = CompanyMember.objects.get(company=company, user=request.user)
                report.prepared_by = member
            except CompanyMember.DoesNotExist:
                pass

            report.save()
            messages.success(request, 'گزارش HSE با موفقیت ایجاد شد.')
            return redirect('hse_report_detail', company_id=company.id, report_id=report.id)
    else:
        form = HSEReportForm(company=company)

    context = {
        'form': form,
        'company': company,
        'page_title': 'ایجاد گزارش HSE جدید'
    }
    return render(request, 'hse/hse_report/create.html', context)


# ==================== Dashboard Views ====================
@login_required_company_member
def dashboard(request, company_id):
    """داشبورد اصلی"""
    company = get_object_or_404(Company, id=company_id)

    # آمار کلی
    stats = {
        'departments': company.departments.filter(is_active=True).count(),
        'members': company.members.filter(is_active=True).count(),
        'inspections': company.inspections.count(),
        'incidents': company.incidents.count(),
        'tasks': company.tasks.count(),
        'completed_tasks': company.tasks.filter(status='COMPLETED').count(),
    }

    # بازرسی‌های اخیر
    recent_inspections = company.inspections.all().order_by('-created_at')[:5]

    # حوادث اخیر
    recent_incidents = company.incidents.all().order_by('-incident_date')[:5]

    # وظایف فوری
    urgent_tasks = company.tasks.filter(
        priority__in=['HIGH', 'URGENT'],
        status__in=['PENDING', 'IN_PROGRESS']
    ).order_by('due_date')[:5]

    # آمار ماهانه حوادث
    today = timezone.now()
    six_months_ago = today - timedelta(days=180)

    monthly_incidents = []
    for i in range(6):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        count = company.incidents.filter(
            incident_date__range=[month_start, month_end]
        ).count()

        monthly_incidents.append({
            'month': month_start.strftime('%Y-%m'),
            'name': month_start.strftime('%b'),
            'count': count
        })

    monthly_incidents.reverse()

    context = {
        'company': company,
        'stats': stats,
        'recent_inspections': recent_inspections,
        'recent_incidents': recent_incidents,
        'urgent_tasks': urgent_tasks,
        'monthly_incidents': monthly_incidents,
        'page_title': f'داشبورد {company.name}'
    }
    return render(request, 'hse/dashboard.html', context)


# ==================== API Views for AJAX ====================
@login_required_company_member
@require_GET
def get_company_stats(request, company_id):
    """دریافت آمار شرکت برای AJAX"""
    company = get_object_or_404(Company, id=company_id)

    # محاسبه آمار
    inspections = company.inspections.all()
    incidents = company.incidents.all()
    tasks = company.tasks.all()

    stats = {
        'inspections': {
            'total': inspections.count(),
            'completed': inspections.filter(status='COMPLETED').count(),
            'in_progress': inspections.filter(status='IN_PROGRESS').count(),
        },
        'incidents': {
            'total': incidents.count(),
            'resolved': incidents.filter(status='RESOLVED').count(),
            'severe': incidents.filter(severity_level='SEVERE').count(),
        },
        'tasks': {
            'total': tasks.count(),
            'completed': tasks.filter(status='COMPLETED').count(),
            'overdue': tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=['PENDING', 'IN_PROGRESS']
            ).count(),
        }
    }

    return JsonResponse(stats)


@login_required_company_member
@require_GET
def search(request, company_id):
    """جستجوی سراسری"""
    company = get_object_or_404(Company, id=company_id)
    query = request.GET.get('q', '').strip()

    results = {
        'inspections': [],
        'incidents': [],
        'tasks': [],
        'members': [],
    }

    if query:
        # جستجو در بازرسی‌ها
        inspections = company.inspections.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        results['inspections'] = [
            {'id': i.id, 'title': i.title, 'status': i.get_status_display()}
            for i in inspections
        ]

        # جستجو در حوادث
        incidents = company.incidents.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        results['incidents'] = [
            {'id': i.id, 'title': i.title, 'severity': i.get_severity_level_display()}
            for i in incidents
        ]

        # جستجو در وظایف
        tasks = company.tasks.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        results['tasks'] = [
            {'id': t.id, 'title': t.title, 'status': t.get_status_display()}
            for t in tasks
        ]

        # جستجو در اعضا
        members = company.members.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(position__icontains=query)
        )[:5]
        results['members'] = [
            {'id': m.id, 'name': str(m.user), 'position': m.get_position_display()}
            for m in members
        ]

    return JsonResponse(results)



# views.py - اضافه کردن view جستجوی کاربران
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@login_required_company_member
@require_GET
def search_users(request):
    """جستجوی کاربران برای AJAX"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'users': []})

    # جستجو در کاربران
    users = CustomUser.objects.filter(
        Q(mobileNumber__icontains=query) |
        Q(name__icontains=query) |
        Q(family__icontains=query) |
        Q(email__icontains=query)
    )[:10]

    users_data = [
        {
            'id': str(user.id),
            'mobileNumber': user.mobileNumber,
            'email': user.email or '',
            'name': f"{user.name or ''} {user.family or ''}".strip() or user.mobileNumber,
        }
        for user in users
    ]

    return JsonResponse({'users': users_data})





from django.contrib.auth.decorators import login_required
from .models import Invitation, Notification

@login_required_company_member
def user_pending_invitations(request):
    """نمایش دعوت‌نامه‌های pending کاربر"""
    pending_invitations = Invitation.objects.filter(
        invited_user=request.user,
        status='PENDING'
    ).select_related('company', 'inviter', 'department').order_by('-created_at')

    context = {
        'pending_invitations': pending_invitations,
        'page_title': 'دعوت‌نامه‌های در انتظار'
    }
    return render(request, "user_app/pending_invitations.html", context)





from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required_company_member
@require_POST
def mark_all_notifications_read(request):
    """علامت‌گذاری همه اعلان‌های کاربر به عنوان خوانده شده"""
    try:
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        count = notifications.count()
        notifications.update(is_read=True)

        return JsonResponse({
            'success': True,
            'message': f'{count} اعلان به عنوان خوانده شده علامت‌گذاری شد',
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@login_required_company_member
@require_GET
def notification_unread_count(request):
    """تعداد اعلان‌های خوانده نشده (برای navbar)"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required_company_member
def notification_detail(request, notification_id):
    """جزئیات اعلان"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)

    # علامت‌گذاری به عنوان خوانده شده
    if not notification.is_read:
        notification.is_read = True
        notification.save()

    # بررسی نوع اعلان و پیدا کردن شی مرتبط
    related_object = None
    related_object_type = None

    if notification.related_object_id and notification.related_object_type:
        related_object_type = notification.related_object_type

        if related_object_type == 'invitation':
            try:
                from .models import Invitation
                related_object = Invitation.objects.get(id=notification.related_object_id)
            except Invitation.DoesNotExist:
                related_object = None
        elif related_object_type == 'member':
            try:
                from .models import CompanyMember
                related_object = CompanyMember.objects.get(id=notification.related_object_id)
            except CompanyMember.DoesNotExist:
                related_object = None
        elif related_object_type == 'task':
            try:
                from .models import Task
                related_object = Task.objects.get(id=notification.related_object_id)
            except Task.DoesNotExist:
                related_object = None

    context = {
        'notification': notification,
        'related_object': related_object,
        'related_object_type': related_object_type,
        'page_title': 'جزئیات اعلان'
    }

    return render(request, 'hse/notification/detail.html', context)




# apps/hse/views.py - بخش آموزش‌ها
from django.http import JsonResponse
from .forms import TrainingCreateForm, TrainingUpdateForm

# ========== Training URLs ==========
from .models import Training,TrainingCategory,TrainingParticipation

@login_required_company_member
def training_list(request, company_id):
    """لیست آموزش‌ها"""
    company = get_object_or_404(Company, id=company_id)

    trainings = Training.objects.filter(company=company)

    # فیلترها
    type_filter = request.GET.get('training_type')
    status_filter = request.GET.get('status')
    department_filter = request.GET.get('department')

    if type_filter:
        trainings = trainings.filter(training_type=type_filter)
    if status_filter:
        trainings = trainings.filter(status=status_filter)
    if department_filter:
        trainings = trainings.filter(department_id=department_filter)

    departments = CompanyDepartment.objects.filter(company=company)

    context = {
        'company': company,
        'trainings': trainings,
        'departments': departments,
        'training_type_choices': Training.TRAINING_TYPE_CHOICES,
        'training_status_choices': Training.STATUS_CHOICES,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'department_filter': department_filter,
    }
    return render(request, 'hse/training/list.html', context)


@login_required_company_member
def training_create(request, company_id):
    """ایجاد آموزش جدید"""
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = TrainingCreateForm(request.POST, request.FILES)
        if form.is_valid():
            training = form.save(commit=False)
            training.company = company
            training.created_by = request.user
            training.save()
            form.save_m2m()  # برای ذخیره شرکت‌کنندگان
            messages.success(request, 'آموزش با موفقیت ایجاد شد.')
            return redirect('hse:training_list', company_id=company.id)
    else:
        form = TrainingCreateForm()

    # فیلتر کردن اعضای شرکت
    members = CompanyMember.objects.filter(company=company, status='ACTIVE')
    departments = CompanyDepartment.objects.filter(company=company)

    form.fields['instructor'].queryset = members
    form.fields['participants'].queryset = members
    form.fields['department'].queryset = departments

    context = {
        'company': company,
        'form': form,
        'members': members,
    }
    return render(request, 'hse/training/create.html', context)


@login_required_company_member
def training_detail(request, company_id, training_id):
    """جزئیات آموزش"""
    company = get_object_or_404(Company, id=company_id)
    training = get_object_or_404(Training, id=training_id, company=company)

    # شرکت‌کنندگان
    participants = training.participants.all()

    # سوابق حضور
    participation_records = TrainingParticipation.objects.filter(training=training)

    context = {
        'company': company,
        'training': training,
        'participants': participants,
        'participation_records': participation_records,
    }
    return render(request, 'hse/training/detail.html', context)


@login_required_company_member
def training_update(request, company_id, training_id):
    """ویرایش آموزش"""
    company = get_object_or_404(Company, id=company_id)
    training = get_object_or_404(Training, id=training_id, company=company)

    if request.method == 'POST':
        form = TrainingUpdateForm(request.POST, request.FILES, instance=training)
        if form.is_valid():
            # اگر وضعیت به تکمیل شده تغییر کرد و تاریخ تکمیل وجود ندارد
            if form.cleaned_data['status'] == 'COMPLETED' and not form.cleaned_data['completion_date']:
                training.completion_date = timezone.now()

            form.save()
            messages.success(request, 'آموزش با موفقیت به‌روزرسانی شد.')
            return redirect('hse:training_detail', company_id=company.id, training_id=training.id)
    else:
        form = TrainingUpdateForm(instance=training)

    # فیلتر کردن اعضای شرکت
    members = CompanyMember.objects.filter(company=company, status='ACTIVE')
    departments = CompanyDepartment.objects.filter(company=company)

    form.fields['instructor'].queryset = members
    form.fields['participants'].queryset = members
    form.fields['department'].queryset = departments

    context = {
        'company': company,
        'training': training,
        'form': form,
    }
    return render(request, 'hse/training/update.html', context)


@login_required_company_member
def training_delete(request, company_id, training_id):
    """حذف آموزش"""
    company = get_object_or_404(Company, id=company_id)
    training = get_object_or_404(Training, id=training_id, company=company)

    if request.method == 'POST':
        training.delete()
        messages.success(request, 'آموزش با موفقیت حذف شد.')
        return redirect('hse:training_list', company_id=company.id)

    context = {
        'company': company,
        'training': training,
    }
    return render(request, 'hse/training/delete.html', context)


@login_required_company_member
def training_update_status(request, company_id, training_id):
    """تغییر وضعیت آموزش"""
    company = get_object_or_404(Company, id=company_id)
    training = get_object_or_404(Training, id=training_id, company=company)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        # بررسی معتبر بودن وضعیت
        valid_statuses = [choice[0] for choice in Training.STATUS_CHOICES]

        if new_status in valid_statuses:
            training.status = new_status

            # اگر وضعیت به تکمیل شده تغییر کرد
            if new_status == 'COMPLETED' and not training.completion_date:
                training.completion_date = timezone.now()

            training.save()
            messages.success(request, f'وضعیت آموزش به {training.get_status_display()} تغییر کرد.')

        return redirect('hse:training_detail', company_id=company.id, training_id=training.id)


@login_required_company_member
def training_register_participant(request, company_id, training_id):
    """ثبت‌نام شرکت‌کننده در آموزش"""
    company = get_object_or_404(Company, id=company_id)
    training = get_object_or_404(Training, id=training_id, company=company)

    if request.method == 'POST':
        participant_id = request.POST.get('participant_id')

        try:
            participant = CompanyMember.objects.get(id=participant_id, company=company)

            # بررسی وجود قبلی
            if not TrainingParticipation.objects.filter(training=training, participant=participant).exists():
                TrainingParticipation.objects.create(
                    training=training,
                    participant=participant,
                    attendance_status='REGISTERED'
                )
                messages.success(request, f'{participant.user.full_name} با موفقیت ثبت‌نام شد.')
            else:
                messages.warning(request, 'این فرد قبلاً ثبت‌نام شده است.')

        except CompanyMember.DoesNotExist:
            messages.error(request, 'شرکت‌کننده یافت نشد.')

    return redirect('hse:training_detail', company_id=company.id, training_id=training.id)


@login_required_company_member
def training_update_participation(request, company_id, training_id, participation_id):
    """به‌روزرسانی وضعیت حضور"""
    company = get_object_or_404(Company, id=company_id)
    training = get_object_or_404(Training, id=training_id, company=company)

    participation = get_object_or_404(TrainingParticipation, id=participation_id, training=training)

    if request.method == 'POST':
        attendance_status = request.POST.get('attendance_status')
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback')
        test_score = request.POST.get('test_score')

        # به‌روزرسانی وضعیت حضور
        if attendance_status in [choice[0] for choice in TrainingParticipation.ATTENDANCE_CHOICES]:
            participation.attendance_status = attendance_status

            if attendance_status == 'ATTENDED' and not participation.attended_at:
                participation.attended_at = timezone.now()

        # به‌روزرسانی ارزیابی
        if rating:
            try:
                participation.participant_rating = int(rating)
            except ValueError:
                pass

        if feedback:
            participation.participant_feedback = feedback

        if test_score:
            try:
                participation.test_score = int(test_score)
            except ValueError:
                pass

        participation.save()
        messages.success(request, 'وضعیت حضور به‌روزرسانی شد.')

    return redirect('hse:training_detail', company_id=company.id, training_id=training.id)


@login_required_company_member
def ai_assistant(request):
    """صفحه دستیار هوشمند HSE"""
    return render(request, 'hse/ai/ai.html')






def serviceLst(request):

    return render(request,'hse/service/servicelist.html')