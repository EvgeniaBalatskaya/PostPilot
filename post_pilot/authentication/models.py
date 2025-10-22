from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_email_confirmed = models.BooleanField(default=False, verbose_name='Email подтверждён')


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Recipient(models.Model):
    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='recipient_list'
    )
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'email']

    def __str__(self):
        return self.email


class Message(models.Model):
    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='messages',
        null=True
    )

    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CHOICES = [
        ('Создана', 'Создана'),
        ('Запущена', 'Запущена'),
        ('Завершена', 'Завершена'),
    ]
    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='mailings',
        null=True
    )

    start_time = models.DateTimeField(null=True, blank=True, verbose_name='Начало отправки')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='Завершение отправки')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Создана', verbose_name='Статус')
    message = models.ForeignKey('Message', on_delete=models.CASCADE, verbose_name='Сообщение')
    recipients = models.ManyToManyField('Recipient', verbose_name='Получатели')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Рассылка #{self.id} - {self.status}"

class MailingAttempt(models.Model):
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts')
    attempted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Успешно', 'Успешно'), ('Не успешно', 'Не успешно')])
    server_response = models.TextField(blank=True, null=True)


