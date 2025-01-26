from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .services import SMSService

def generate_sms_code():
    """Генерация 4-значного кода"""
    return ''.join(random.choices(string.digits, k=4))

class User(AbstractUser):
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        unique=True,
        help_text=_('Required. Format: +7XXXXXXXXXX'),
    )
    sms_code = models.CharField('SMS код', max_length=4, blank=True, null=True)
    sms_code_expires = models.DateTimeField('Срок действия кода', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Решаем конфликт с обратными отношениями
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']  # username остается для совместимости
    
    def set_sms_code(self):
        """Установить новый SMS код"""
        self.sms_code = generate_sms_code()
        self.sms_code_expires = timezone.now() + timezone.timedelta(minutes=5)
        self.save()
        return self.sms_code
    
    def verify_sms_code(self, code):
        """Проверить SMS код"""
        if not self.sms_code or not self.sms_code_expires:
            return False
        if timezone.now() > self.sms_code_expires:
            return False
        return self.sms_code == code

    def __str__(self):
        return self.phone or self.username

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class OneTimeCode(models.Model):
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        help_text=_('Phone number in format: +7XXXXXXXXXX')
    )
    code = models.CharField(
        _('verification code'),
        max_length=4,
        help_text=_('4-digit verification code')
    )
    attempts = models.IntegerField(
        _('verification attempts'),
        default=0,
        help_text=_('Number of verification attempts')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('Code expiration time')
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether the code has been verified')
    )
    
    class Meta:
        verbose_name = _('one time code')
        verbose_name_plural = _('one time codes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', 'is_verified']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.phone}: {self.code}"
    
    def is_expired(self) -> bool:
        """Проверка истечения срока действия кода"""
        return timezone.now() > self.expires_at
    
    def is_blocked(self) -> bool:
        """Проверка блокировки после превышения попыток"""
        return self.attempts >= 3
    
    @classmethod
    def generate_code(cls, phone: str) -> 'OneTimeCode':
        """Создание нового кода подтверждения"""
        # Очищаем старые коды
        cls.objects.filter(phone=phone).delete()
        
        # Создаем новый код
        code = SMSService.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=5)
        
        return cls.objects.create(
            phone=phone,
            code=code,
            expires_at=expires_at
        )
    
    def verify(self, input_code: str) -> bool:
        """Проверка кода подтверждения"""
        if self.is_verified:
            return False
            
        if self.is_expired():
            return False
            
        if self.is_blocked():
            return False
            
        if self.code != input_code:
            self.attempts += 1
            self.save()
            return False
            
        self.is_verified = True
        self.save()
        return True
    
    def clean(self):
        """Валидация модели"""
        if not self.code.isdigit() or len(self.code) != 4:
            raise ValidationError({
                'code': _('Code must be exactly 4 digits')
            })
        
        if self.expires_at <= timezone.now():
            raise ValidationError({
                'expires_at': _('Expiration time must be in the future')
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
