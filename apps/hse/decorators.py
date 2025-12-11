# apps/hse/decorators.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import Company, CompanyMember

def require_company_access(permission='view'):
    """
    دکوراتور ساده برای دسترسی به پنل شرکت
    permission: 'view' یا 'edit' یا 'manage'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # گرفتن company_id از URL
            company_id = kwargs.get('company_id') or kwargs.get('pk')

            if not company_id:
                return view_func(request, *args, **kwargs)

            # پیدا کردن شرکت
            company = get_object_or_404(Company, id=company_id)

            # 1. اگر کاربر صاحب شرکت است → همه دسترسی‌ها
            if company.user == request.user:
                return view_func(request, *args, **kwargs)

            # 2. اگر کاربر عضو شرکت است → بررسی سمت
            try:
                member = CompanyMember.objects.get(
                    company=company,
                    user=request.user,
                    is_active=True
                )

                # اگر مدیر/ناظر است → همه دسترسی‌ها
                if member.position in ['MANAGER', 'SUPERVISOR']:
                    return view_func(request, *args, **kwargs)

                # اگر کارشناس است → مشاهده + ویرایش
                if member.position == 'EXPERT' and permission in ['view', 'edit']:
                    return view_func(request, *args, **kwargs)

                # اگر اپراتور/کارگر است → فقط مشاهده
                if member.position in ['OPERATOR', 'WORKER', 'OTHER'] and permission == 'view':
                    return view_func(request, *args, **kwargs)

            except CompanyMember.DoesNotExist:
                pass

            # اگر به اینجا رسیدیم یعنی دسترسی ندارد
            raise PermissionDenied("شما دسترسی لازم به این قسمت را ندارید")

        return _wrapped_view
    return decorator


def company_access(view_func):
    """
    دکوراتور خیلی ساده: اگر صاحب شرکت یا مدیر/ناظر هست → بده بره
    برای اکثر پنل‌ها کافی است
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        company_id = kwargs.get('company_id') or kwargs.get('pk')

        if not company_id:
            return view_func(request, *args, **kwargs)

        company = get_object_or_404(Company, id=company_id)

        # اگر صاحب شرکت است
        if company.user == request.user:
            return view_func(request, *args, **kwargs)

        # اگر مدیر/ناظر شرکت است
        try:
            member = CompanyMember.objects.get(
                company=company,
                user=request.user,
                is_active=True,
                position__in=['MANAGER', 'SUPERVISOR']
            )
            return view_func(request, *args, **kwargs)
        except CompanyMember.DoesNotExist:
            pass

        # اگر به اینجا رسیدیم یعنی دسترسی ندارد
        raise PermissionDenied("فقط صاحب شرکت یا مدیران می‌توانند به این قسمت دسترسی داشته باشند")

    return _wrapped_view


def company_member_access(view_func):
    """
    دکوراتور برای دسترسی همه اعضای شرکت
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        company_id = kwargs.get('company_id') or kwargs.get('pk')

        if not company_id:
            return view_func(request, *args, **kwargs)

        # پیدا کردن شرکت (بدون شرط user)
        company = get_object_or_404(Company, id=company_id)

        # اگر صاحب شرکت است
        if company.user == request.user:
            # اضافه کردن اطلاعات به request برای استفاده در view
            request.company = company
            request.user_is_owner = True
            return view_func(request, *args, **kwargs)

        # اگر عضو فعال شرکت است
        try:
            member = CompanyMember.objects.get(
                company=company,
                user=request.user,
                is_active=True
            )
            # اضافه کردن اطلاعات به request
            request.company = company
            request.user_is_owner = False
            request.member = member
            return view_func(request, *args, **kwargs)
        except CompanyMember.DoesNotExist:
            pass

        # اگر به اینجا رسیدیم یعنی دسترسی ندارد
        raise PermissionDenied("شما عضو این شرکت نیستید")

    return _wrapped_view





def login_required_company_member(view_func):
    """
    ترکیب login_required و company_member_access در یک دکوراتور
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # اول بررسی لاگین بودن
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            from django.urls import reverse
            return redirect_to_login(
                request.get_full_path(),
                reverse('account:send_mobile')
            )

        # سپس بررسی دسترسی شرکت
        company_id = kwargs.get('company_id') or kwargs.get('pk')

        if not company_id:
            return view_func(request, *args, **kwargs)

        company = get_object_or_404(Company, id=company_id)

        # اگر صاحب شرکت است
        if company.user == request.user:
            request.company = company
            request.user_is_owner = True
            return view_func(request, *args, **kwargs)

        # اگر عضو فعال شرکت است
        try:
            member = CompanyMember.objects.get(
                company=company,
                user=request.user,
                is_active=True
            )
            request.company = company
            request.user_is_owner = False
            request.member = member
            return view_func(request, *args, **kwargs)
        except CompanyMember.DoesNotExist:
            pass

        raise PermissionDenied("شما عضو این شرکت نیستید")

    return _wrapped_view