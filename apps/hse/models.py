from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.user.model.user import CustomUser
import uuid
from datetime import date



class Company(models.Model):
    """مدل شرکت"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='companies',
        verbose_name='کاربر ایجادکننده'
    )
    name = models.CharField(max_length=255, verbose_name='نام شرکت')
    activity_field = models.CharField(max_length=255, verbose_name='حوزه فعالیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CompanyDepartment(models.Model):
    """مدل بخش شرکت"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='شرکت'
    )
    name = models.CharField(max_length=255, verbose_name='نام بخش')
    employee_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='تعداد کارکنان'
    )
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='مدیر بخش'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'بخش شرکت'
        verbose_name_plural = 'بخش‌های شرکت'
        unique_together = ['company', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.company.name}"


class CompanyMember(models.Model):
    """مدل همکاران شرکت"""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'فعال'
        INACTIVE = 'INACTIVE', 'غیرفعال'
        SUSPENDED = 'SUSPENDED', 'تعلیق شده'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='شرکت'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='company_memberships',
        verbose_name='کاربر'
    )
    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name='بخش'
    )

    class Position(models.TextChoices):
        MANAGER = 'MANAGER', 'مدیر'
        SUPERVISOR = 'SUPERVISOR', 'ناظر'
        EXPERT = 'EXPERT', 'کارشناس'
        OPERATOR = 'OPERATOR', 'اپراتور'
        WORKER = 'WORKER', 'کارگر'
        OTHER = 'OTHER', 'سایر'

    position = models.CharField(
        max_length=50,
        choices=Position.choices,
        default=Position.WORKER,
        verbose_name='سمت'
    )

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='وضعیت'
    )

    join_date = models.DateField(auto_now_add=True, verbose_name='تاریخ عضویت')
    leave_date = models.DateField(null=True, blank=True, verbose_name='تاریخ ترک')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'عضو شرکت'
        verbose_name_plural = 'اعضای شرکت'
        unique_together = ['company', 'user']
        ordering = ['-join_date']

    def __str__(self):
        return f"{self.user} - {self.company.name} ({self.get_position_display()})"

# apps/hse/models.py
class Inspection(models.Model):
    """مدل بازرسی‌ها"""

    # اولویت‌ها
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

    PRIORITY_CHOICES = [
        (LOW, 'پایین'),
        (MEDIUM, 'متوسط'),
        (HIGH, 'بالا'),
        (CRITICAL, 'بحرانی'),
    ]

    # وضعیت‌ها
    DRAFT = 'DRAFT'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (DRAFT, 'پیش‌نویس'),
        (IN_PROGRESS, 'در حال انجام'),
        (COMPLETED, 'تکمیل شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name='شرکت'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان بازرسی')
    description = models.TextField(blank=True, verbose_name='توضیحات')

    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_CHOICES,
        default=MEDIUM,
        verbose_name='اولویت'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name='وضعیت'
    )

    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspections',
        verbose_name='بخش'
    )

    assigned_to = models.ForeignKey(
        CompanyMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_inspections',
        verbose_name='واگذار شده به'
    )

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_inspections',
        verbose_name='ایجاد کننده'
    )

    scheduled_date = models.DateField(verbose_name='تاریخ برنامه‌ریزی')
    completed_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تکمیل')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'بازرسی'
        verbose_name_plural = 'بازرسی‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

class Incident(models.Model):
    """مدل حوادث و خطرات"""

    # انواع حادثه
    INCIDENT_TYPE_CHOICES = [
        ('OCCURRED', 'اتفاق افتاده'),
        ('POTENTIAL', 'احتمالی'),
        ('NEAR_MISS', 'شبه‌حادثه'),
    ]

    # سطح حادثه
    SEVERITY_CHOICES = [
        ('LOW', 'پایین'),
        ('MEDIUM', 'متوسط'),
        ('HIGH', 'بالا'),
        ('SEVERE', 'شدید'),
    ]

    # وضعیت حادثه
    STATUS_CHOICES = [
        ('UNDER_INVESTIGATION', 'در حال بررسی'),
        ('REPORTED', 'گزارش شده'),
        ('RESOLVED', 'حل شده'),
        ('CLOSED', 'بسته شده'),
        ('PENDING', 'در انتظار'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='incidents',
        verbose_name='شرکت'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان حادثه')
    description = models.TextField(verbose_name='توضیحات')

    incident_type = models.CharField(
        max_length=50,
        choices=INCIDENT_TYPE_CHOICES,
        verbose_name='نوع حادثه'
    )

    severity_level = models.CharField(
        max_length=50,
        choices=SEVERITY_CHOICES,
        default='MEDIUM',
        verbose_name='سطح حادثه'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='UNDER_INVESTIGATION',
        verbose_name='وضعیت حادثه'
    )

    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        verbose_name='بخش مرتبط'
    )

    reporter = models.ForeignKey(
        CompanyMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_incidents',
        verbose_name='گزارش دهنده'
    )

    incident_date = models.DateTimeField(verbose_name='تاریخ وقوع حادثه')
    location = models.CharField(max_length=500, blank=True, verbose_name='محل وقوع')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'حادثه'
        verbose_name_plural = 'حوادث'
        ordering = ['-incident_date']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

class Task(models.Model):
    """مدل وظایف"""

    # اولویت‌ها - به صورت لیست ساده
    PRIORITY_CHOICES = [
        ('LOW', 'پایین'),
        ('MEDIUM', 'متوسط'),
        ('HIGH', 'بالا'),
        ('URGENT', 'فوری'),
    ]

    # وضعیت‌ها - به صورت لیست ساده
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('IN_PROGRESS', 'در حال انجام'),
        ('UNDER_REVIEW', 'در حال بررسی'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='شرکت'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان وظیفه')
    description = models.TextField(blank=True, verbose_name='توضیحات')

    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',  # مقدار پیش‌فرض به صورت string
        verbose_name='اولویت'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PENDING',  # مقدار پیش‌فرض به صورت string
        verbose_name='وضعیت'
    )

    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='بخش مرتبط'
    )

    assigned_to = models.ForeignKey(
        CompanyMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='مسئول'
    )

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='ایجاد شده توسط'
    )

    due_date = models.DateField(null=True, blank=True, verbose_name='تاریخ سررسید')
    completed_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تکمیل')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    # ارتباط با سایر مدل‌ها (اختیاری)
    related_inspection = models.ForeignKey(
        Inspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='بازرسی مرتبط'
    )

    related_incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='حادثه مرتبط'
    )

    class Meta:
        verbose_name = 'وظیفه'
        verbose_name_plural = 'وظایف'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"


class Invitation(models.Model):
    """مدل دعوت‌نامه‌ها"""

    # حذف کلاس Status و استفاده از string ساده
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('ACCEPTED', 'پذیرفته شده'),
        ('REJECTED', 'رد شده'),
        ('EXPIRED', 'منقضی شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='شرکت'
    )

    invited_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='کاربر دعوت شده',
        null=True,
        blank=True
    )

    invited_mobile = models.CharField(
        max_length=11,
        verbose_name='شماره موبایل دعوت شده',
        null=True,
        blank=True
    )

    inviter = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
        verbose_name='دعوت کننده'
    )

    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='بخش پیشنهادی'
    )

    position = models.CharField(
        max_length=50,
        choices=CompanyMember.Position.choices,
        default='WORKER',
        verbose_name='سمت پیشنهادی'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='وضعیت'
    )

    message = models.TextField(blank=True, verbose_name='پیام دعوت')
    token = models.CharField(max_length=100, unique=True, verbose_name='توکن')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پاسخ')

    class Meta:
        verbose_name = 'دعوت‌نامه'
        verbose_name_plural = 'دعوت‌نامه‌ها'
        ordering = ['-created_at']

    def __str__(self):
        if self.invited_user:
            return f"دعوت {self.invited_user} به {self.company.name}"
        return f"دعوت شماره {self.token} به {self.company.name}"


    def is_expired(self):
        """بررسی انقضای دعوت - کاملاً ایمن"""
        from django.utils import timezone

        # اگر expires_at وجود نداشته باشد، دعوت منقضی محسوب نمی‌شود
        if not self.expires_at:
            return False

        # فقط دعوت‌نامه‌های PENDING می‌توانند منقضی شوند
        if self.status != 'PENDING':
            return False

        # مقایسه زمان‌ها
        try:
            return timezone.now() > self.expires_at
        except (TypeError, AttributeError):
            # در صورت هرگونه خطا در مقایسه
            return False

    @property
    def is_active(self):
        """بررسی فعال بودن دعوت (در انتظار و منقضی نشده)"""
        return self.status == 'PENDING' and not self.is_expired
    @property
    def is_active(self):
        """بررسی فعال بودن دعوت (در انتظار و منقضی نشده)"""
        return self.status == 'PENDING' and not self.is_expired()



class Notification(models.Model):
    """مدل اعلان‌ها"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='کاربر'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان')
    message = models.TextField(verbose_name='پیام')

    class NotificationType(models.TextChoices):
        INVITATION = 'INVITATION', 'دعوت'
        TASK_ASSIGNED = 'TASK_ASSIGNED', 'وظیفه محول شده'
        INSPECTION_REMINDER = 'INSPECTION_REMINDER', 'یادآوری بازرسی'
        INCIDENT_REPORT = 'INCIDENT_REPORT', 'گزارش حادثه'
        SYSTEM = 'SYSTEM', 'سیستمی'
        WARNING = 'WARNING', 'هشدار'

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        verbose_name='نوع اعلان'
    )

    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    related_object_id = models.UUIDField(null=True, blank=True, verbose_name='آیدی شی مرتبط')
    related_object_type = models.CharField(max_length=100, blank=True, verbose_name='نوع شی مرتبط')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user}"


class HSEReport(models.Model):
    """مدل گزارشات HSE"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='hse_reports',
        verbose_name='شرکت'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان گزارش')

    class ReportType(models.TextChoices):
        MONTHLY = 'MONTHLY', 'ماهانه'
        QUARTERLY = 'QUARTERLY', 'فصلی'
        YEARLY = 'YEARLY', 'سالانه'
        INCIDENT = 'INCIDENT', 'حادثه'
        INSPECTION = 'INSPECTION', 'بازرسی'
        SAFETY = 'SAFETY', 'ایمنی'
        ENVIRONMENTAL = 'ENVIRONMENTAL', 'محیط زیستی'
        HEALTH = 'HEALTH', 'بهداشتی'

    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices,
        verbose_name='نوع گزارش'
    )

    period_start = models.DateField(verbose_name='شروع دوره')
    period_end = models.DateField(verbose_name='پایان دوره')

    # آمارها
    total_incidents = models.IntegerField(default=0, verbose_name='تعداد کل حوادث')
    serious_incidents = models.IntegerField(default=0, verbose_name='حوادث شدید')
    minor_incidents = models.IntegerField(default=0, verbose_name='حوادث جزئی')
    near_misses = models.IntegerField(default=0, verbose_name='شبه حوادث')

    total_inspections = models.IntegerField(default=0, verbose_name='تعداد بازرسی‌ها')
    completed_inspections = models.IntegerField(default=0, verbose_name='بازرسی‌های تکمیل شده')
    pending_inspections = models.IntegerField(default=0, verbose_name='بازرسی‌های در انتظار')

    total_tasks = models.IntegerField(default=0, verbose_name='تعداد وظایف')
    completed_tasks = models.IntegerField(default=0, verbose_name='وظایف تکمیل شده')
    overdue_tasks = models.IntegerField(default=0, verbose_name='وظایف معوقه')

    # شاخص‌های HSE
    accident_frequency_rate = models.FloatField(default=0, verbose_name='نرخ فراوانی حوادث')
    accident_severity_rate = models.FloatField(default=0, verbose_name='نرخ شدت حوادث')
    safety_performance_index = models.FloatField(default=0, verbose_name='شاخص عملکرد ایمنی')

    recommendations = models.TextField(blank=True, verbose_name='توصیه‌ها')
    conclusions = models.TextField(blank=True, verbose_name='نتیجه‌گیری')

    prepared_by = models.ForeignKey(
        CompanyMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prepared_reports',
        verbose_name='تهیه کننده'
    )

    approved_by = models.ForeignKey(
        CompanyMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reports',
        verbose_name='تایید کننده'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'گزارش HSE'
        verbose_name_plural = 'گزارشات HSE'
        ordering = ['-period_end']

    def __str__(self):
        return f"{self.title} - {self.company.name}"



# apps/hse/models.py
class Training(models.Model):
    """مدل آموزش‌های HSE"""

    # انواع آموزش
    TRAINING_TYPE_CHOICES = [
        ('SAFETY', 'ایمنی'),
        ('ENVIRONMENTAL', 'محیط زیستی'),
        ('HEALTH', 'بهداشتی'),
        ('FIRE', 'اطفاء حریق'),
        ('FIRST_AID', 'کمک‌های اولیه'),
        ('ERGONOMIC', 'ارگونومی'),
        ('CHEMICAL', 'مواد شیمیایی'),
        ('EQUIPMENT', 'تجهیزات'),
    ]

    # سطح آموزش
    LEVEL_CHOICES = [
        ('BASIC', 'مقدماتی'),
        ('INTERMEDIATE', 'متوسط'),
        ('ADVANCED', 'پیشرفته'),
    ]

    # وضعیت آموزش
    STATUS_CHOICES = [
        ('PLANNED', 'برنامه‌ریزی شده'),
        ('IN_PROGRESS', 'در حال اجرا'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='trainings',
        verbose_name='شرکت'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان آموزش')
    description = models.TextField(blank=True, verbose_name='توضیحات آموزش')

    training_type = models.CharField(
        max_length=50,
        choices=TRAINING_TYPE_CHOICES,
        verbose_name='نوع آموزش'
    )

    level = models.CharField(
        max_length=50,
        choices=LEVEL_CHOICES,
        default='BASIC',
        verbose_name='سطح آموزش'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PLANNED',
        verbose_name='وضعیت آموزش'
    )

    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainings',
        verbose_name='بخش'
    )

    # فایل ویدیوی آموزش
    video = models.FileField(
        upload_to='trainings/videos/',
        verbose_name='فیلم آموزش',
        null=True,
        blank=True
    )

    # فایل‌های مرتبط (PDF، اسلایدها، ...)
    attachment = models.FileField(
        upload_to='trainings/attachments/',
        null=True,
        blank=True,
        verbose_name='ضمیمه'
    )

    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name='مدت زمان آموزش (دقیقه)'
    )

    # تاریخ‌ها
    scheduled_date = models.DateTimeField(verbose_name='تاریخ و زمان برنامه‌ریزی')
    completion_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')

    # مدرس/ارائه‌دهنده
    instructor = models.ForeignKey(
        CompanyMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instructor_trainings',
        verbose_name='مدرس'
    )

    # ایجادکننده
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_trainings',
        verbose_name='ایجاد کننده'
    )

    # شرکت‌کنندگان
    participants = models.ManyToManyField(
        CompanyMember,
        through='TrainingParticipation',
        related_name='participated_trainings',
        verbose_name='شرکت‌کنندگان',
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'آموزش'
        verbose_name_plural = 'آموزش‌ها'
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def get_video_url(self):
        """دریافت URL فیلم آموزش"""
        if self.video:
            return self.video.url
        return None

    def get_participants_count(self):
        """تعداد شرکت‌کنندگان"""
        return self.participants.count()


class TrainingParticipation(models.Model):
    """مدل حضور در آموزش (برای ثبت جزئیات شرکت‌کنندگان)"""

    # وضعیت حضور
    ATTENDANCE_CHOICES = [
        ('REGISTERED', 'ثبت‌نام شده'),
        ('ATTENDED', 'حاضر شده'),
        ('ABSENT', 'غایب'),
        ('EXCUSED', 'معذور'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        related_name='participation_records',
        verbose_name='آموزش'
    )
    participant = models.ForeignKey(
        CompanyMember,
        on_delete=models.CASCADE,
        related_name='training_participations',
        verbose_name='شرکت‌کننده'
    )

    attendance_status = models.CharField(
        max_length=50,
        choices=ATTENDANCE_CHOICES,
        default='REGISTERED',
        verbose_name='وضعیت حضور'
    )

    # ارزیابی شرکت‌کننده از آموزش
    participant_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='امتیاز شرکت‌کننده (1-5)'
    )

    participant_feedback = models.TextField(
        blank=True,
        verbose_name='نظر شرکت‌کننده'
    )

    # آزمون
    test_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='نمره آزمون'
    )

    # گواهی
    certificate_issued = models.BooleanField(default=False, verbose_name='صدور گواهی')
    certificate_issue_date = models.DateField(null=True, blank=True, verbose_name='تاریخ صدور گواهی')

    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت‌نام')
    attended_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ حضور')

    class Meta:
        verbose_name = 'حضور در آموزش'
        verbose_name_plural = 'حضور در آموزش‌ها'
        unique_together = ['training', 'participant']

    def __str__(self):
        return f"{self.participant.user.full_name} در {self.training.title}"


class TrainingCategory(models.Model):
    """دسته‌بندی آموزش‌ها"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='training_categories',
        verbose_name='شرکت'
    )
    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    description = models.TextField(blank=True, verbose_name='توضیحات')

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='دسته‌بندی والد'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'دسته‌بندی آموزش'
        verbose_name_plural = 'دسته‌بندی‌های آموزش'
        ordering = ['name']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.name} - {self.company.name}"