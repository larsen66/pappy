from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator
from .services import SMSService
import random
import logging

# Настройка логирования
logger = logging.getLogger('zaglushka')

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        try:
            if not phone:
                raise ValueError('Номер телефона обязателен')
            user = self.model(phone=phone, **extra_fields)
            if password:
                user.set_password(password)
            user.save(using=self._db)
            return user
        except Exception as e:
            logger.error(f'Ошибка при создании пользователя: {str(e)}', exc_info=True)
            raise
    
    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)

class User(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    
    # Основные поля
    phone = models.CharField(
        _('телефон'), 
        validators=[phone_regex], 
        max_length=17, 
        unique=True
    )
    email = models.EmailField(_('email'), blank=True)
    created_at = models.DateTimeField(
        _('дата регистрации'),
        default=timezone.now
    )
    
    # Статусы пользователя
    is_verified = models.BooleanField(_('верифицирован'), default=False)
    is_seller = models.BooleanField(_('продавец'), default=False)
    is_specialist = models.BooleanField(_('специалист'), default=False)
    is_shelter = models.BooleanField(_('приют'), default=False)
    
    # Дополнительные поля
    rating = models.DecimalField(_('рейтинг'), max_digits=3, decimal_places=2, default=0)
    
    # Настройки Django
    username = None
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
    
    def __str__(self):
        return self.phone

class OneTimeCode(models.Model):
    CODE_LENGTH = 4
    EXPIRY_TIME_MINUTES = 5
    MAX_ATTEMPTS = 3
    
    phone = models.CharField(
        'Номер телефона',
        max_length=17
    )
    code = models.CharField(
        'Код подтверждения',
        max_length=4
    )
    created_at = models.DateTimeField(
        'Создан',
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        'Истекает'
    )
    attempts = models.IntegerField(
        'Попытки',
        default=0
    )
    is_verified = models.BooleanField(
        'Подтвержден',
        default=False
    )

    class Meta:
        verbose_name = 'Код подтверждения'
        verbose_name_plural = 'Коды подтверждения'
        ordering = ['-created_at']

    def __str__(self):
        return f'Код для {self.phone}'

    def is_expired(self):
        """Проверяет, истек ли срок действия кода"""
        return timezone.now() > self.expires_at
    
    def is_blocked(self):
        """Проверяет, не превышено ли количество попыток"""
        return self.attempts >= self.MAX_ATTEMPTS
    
    def verify(self, input_code):
        """Проверяет код и обновляет статус"""
        try:
            if self.is_expired():
                return False, 'Код истек'
            
            if self.is_blocked():
                return False, 'Превышено количество попыток'
            
            if self.code != input_code:
                self.attempts += 1
                self.save()
                return False, 'Неверный код'
            
            self.is_verified = True
            self.save()
            return True, None
            
        except Exception as e:
            logger.error(f'Ошибка при проверке кода: {str(e)}', exc_info=True)
            return False, 'Произошла ошибка при проверке кода'

    @staticmethod
    def generate_code(phone):
        """Генерирует новый код подтверждения"""
        try:
            # Деактивируем старые коды
            OneTimeCode.objects.filter(phone=phone).update(is_verified=True)
            
            # Генерируем новый код
            code = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            
            # Создаем новую запись
            verification = OneTimeCode.objects.create(
                phone=phone,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=OneTimeCode.EXPIRY_TIME_MINUTES)
            )
            
            logger.info(f"Generated new code for {phone}")
            return verification
            
        except Exception as e:
            logger.error(f"Error generating code for {phone}: {str(e)}", exc_info=True)
            raise

class SellerVerification(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_verifications',
        verbose_name='Пользователь'
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    passport_scan = models.FileField(
        'Скан паспорта',
        upload_to='seller_verification/passport'
    )
    selfie_with_passport = models.FileField(
        'Селфи с паспортом',
        upload_to='seller_verification/selfie'
    )
    additional_document = models.FileField(
        'Дополнительный документ',
        upload_to='seller_verification/additional',
        blank=True,
        null=True
    )
    rejection_reason = models.TextField(
        'Причина отказа',
        blank=True
    )
    created = models.DateTimeField(
        'Создано',
        auto_now_add=True
    )
    updated = models.DateTimeField(
        'Обновлено',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Верификация продавца'
        verbose_name_plural = 'Верификации продавцов'
    
    def __str__(self):
        return f'{self.user.get_full_name()} - {self.get_status_display()}'
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if self.status == 'approved' and not is_new and \
           timezone.now() - self.created > timedelta(hours=48):
            self.user.is_seller = True
            self.user.save()

class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    documents = models.JSONField(_('документы'))
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)
    comment = models.TextField(_('комментарий'), blank=True)
    
    class Meta:
        verbose_name = _('запрос на верификацию')
        verbose_name_plural = _('запросы на верификацию')
        ordering = ['-created_at'] 