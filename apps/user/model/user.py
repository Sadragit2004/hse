# apps/user/model/user.py
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
import uuid
from datetime import date
from ..validators.mobile_validator import validate_iranian_mobile


class CustomUserManager(BaseUserManager):

    def create_user(self, mobileNumber, password=None, **extra_fields):
        if not mobileNumber:
            raise ValueError("شماره موبایل الزامی است")

        validate_iranian_mobile(mobileNumber)

        # مقدار default برای role را اضافه می‌کنیم
        extra_fields.setdefault('role', CustomUser.Role.DEFAULT)

        user = self.model(mobileNumber=mobileNumber, **extra_fields)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, mobileNumber, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # استفاده از مقدار string به جای instance
        extra_fields.setdefault("role", "SUPERUSER")  # اینجا string است
        return self.create_user(mobileNumber, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        SUPERUSER = "SUPERUSER", "سوپر کاربر"
        HSE_MANAGER = "HSE_MANAGER", "مدیر HSE"
        HSE_EXPERT = "HSE_EXPERT", "کارشناس HSE"
        RESPONSIBLE = "RESPONSIBLE", "مسئول"
        DEFAULT = "DEFAULT", "کاربر عادی"

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    mobileNumber = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_iranian_mobile],
        verbose_name="شماره موبایل"
    )
    email = models.EmailField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ایمیل"
    )
    name = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="نام"
    )
    family = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="نام خانوادگی"
    )

    GENDER_CHOICES = (
        ("M", "مرد"),
        ("F", "زن")
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default="M",
        verbose_name="جنسیت"
    )

    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاریخ تولد"
    )

    # فیلد نقش (Role)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DEFAULT,  # مقدار default به صورت instance
        verbose_name="نقش"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="کارمند"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ بروزرسانی"
    )

    USERNAME_FIELD = "mobileNumber"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ['-created_at']

    def __str__(self):
        if self.name and self.family:
            return f"{self.name} {self.family}"
        return f"{self.mobileNumber}"

    @property
    def full_name(self):
        if self.name and self.family:
            return f"{self.name} {self.family}"
        return self.mobileNumber

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    # متدهای کمکی برای بررسی نقش‌ها
    def is_hse_manager(self):
        return self.role == self.Role.HSE_MANAGER

    def is_hse_expert(self):
        return self.role == self.Role.HSE_EXPERT

    def is_responsible(self):
        return self.role == self.Role.RESPONSIBLE

    def is_superuser_role(self):
        return self.role == self.Role.SUPERUSER

    def save(self, *args, **kwargs):
        # اطمینان از ذخیره‌سازی صحیح مقدار role
        if isinstance(self.role, self.Role):
            self.role = self.role.value
        super().save(*args, **kwargs)