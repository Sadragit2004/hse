from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.utils import timezone
from ...forms.auth.verify_form import VerificationCodeForm
from ...model.user import CustomUser
from ...service.auth_service import AuthService
from apps.hse.models import Invitation, Notification

def verify_code(request):
    mobile = request.session.get("mobileNumber")
    next_url = request.session.get("next_url")
    if not mobile:
        messages.error(request, "شماره موبایل یافت نشد.")
        return redirect("account:send_mobile")

    try:
        user = CustomUser.objects.get(mobileNumber=mobile)
    except CustomUser.DoesNotExist:
        messages.error(request, "کاربر یافت نشد.")
        return redirect("account:send_mobile")

    security = AuthService.get_or_create_security(user)

    if request.method == "POST":
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['activeCode']
            try:
                AuthService.verify_code(security, code)
                AuthService.activate_user(user)
                login(request, user)

                # ========== بخش جدید: بررسی دعوت‌نامه‌های pending ==========
                # پیدا کردن دعوت‌نامه‌های فعال (نه منقضی شده) برای این شماره موبایل
                current_time = timezone.now()
                active_invitations = Invitation.objects.filter(
                    invited_mobile=mobile,
                    status='PENDING'
                ).exclude(
                    expires_at__isnull=True
                ).filter(
                    expires_at__gt=current_time  # فقط دعوت‌نامه‌های منقضی نشده
                )

                # برای هر دعوت active، یک اعلان ایجاد کن
                for invitation in active_invitations:
                    # اعلان برای کاربر
                    Notification.objects.create(
                        user=user,
                        title=f'دعوت به شرکت {invitation.company.name}',
                        message=f'شما برای عضویت در شرکت {invitation.company.name} دعوت شده‌اید. سمت پیشنهادی: {invitation.get_position_display()}',
                        notification_type='INVITATION',
                        related_object_id=invitation.id,
                        related_object_type='invitation'
                    )

                    # همچنین دعوت‌نامه را به کاربر وصل کن
                    invitation.invited_user = user
                    invitation.save()

                # اگر دعوت active داشت، پیام خاص نشان بده
                if active_invitations.exists():
                    count = active_invitations.count()
                    messages.info(request, f"✅ ثبت‌نام موفق! {count} دعوت‌نامه‌ی فعال دارید.")
                else:
                    messages.success(request, "✅ ورود با موفقیت انجام شد.")
                # ========== پایان بخش جدید ==========

                return redirect(next_url or "main:index")
            except Exception as e:
                messages.error(request, str(e))
                return redirect("account:verify_code")
    else:
        form = VerificationCodeForm()

    return render(request, "user_app/code.html", {"form": form, "mobile": mobile})