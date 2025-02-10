import random
import string

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Введите номер телефона")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password if password else '')
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(phone_number=phone_number, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True, verbose_name='Номер телефона')
    # password = models.CharField(max_length=30, blank=True, null=True, verbose_name='Пароль')
    confirm_code = models.CharField(max_length=4, blank=True, null=True, verbose_name='Код подтверждения')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=False, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Доступ к админке')
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return f"{self.phone_number}, {self.confirm_code}"

    def save(self, *args, **kwargs):
        if not self.confirm_code:
            self.confirm_code = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
