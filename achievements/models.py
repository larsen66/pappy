from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Achievement(models.Model):
    """Модель достижения"""
    CATEGORY_CHOICES = [
        ('activity', _('Активность')),
        ('social', _('Социальная')),
        ('professional', _('Профессиональная')),
        ('special', _('Особая')),
    ]
    
    LEVEL_CHOICES = [
        ('bronze', _('Бронзовый')),
        ('silver', _('Серебряный')),
        ('gold', _('Золотой')),
    ]
    
    name = models.CharField(_('название'), max_length=100)
    description = models.TextField(_('описание'))
    category = models.CharField(_('категория'), max_length=20, choices=CATEGORY_CHOICES)
    level = models.CharField(_('уровень'), max_length=20, choices=LEVEL_CHOICES)
    icon = models.ImageField(_('иконка'), upload_to='achievements/icons/')
    points = models.PositiveIntegerField(_('очки'))
    condition = models.JSONField(_('условие получения'))
    is_active = models.BooleanField(_('активно'), default=True)
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('достижение')
        verbose_name_plural = _('достижения')
        ordering = ['category', 'level', 'points']

class UserAchievement(models.Model):
    """Модель полученного пользователем достижения"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name=_('пользователь')
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements',
        verbose_name=_('достижение')
    )
    earned_at = models.DateTimeField(_('получено'), auto_now_add=True)
    progress = models.JSONField(_('прогресс'), default=dict)
    
    class Meta:
        verbose_name = _('достижение пользователя')
        verbose_name_plural = _('достижения пользователей')
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']

class Badge(models.Model):
    """Модель значка"""
    name = models.CharField(_('название'), max_length=100)
    description = models.TextField(_('описание'))
    icon = models.ImageField(_('иконка'), upload_to='badges/icons/')
    is_special = models.BooleanField(_('особый'), default=False)
    requirements = models.JSONField(_('требования'))
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('значок')
        verbose_name_plural = _('значки')

class UserBadge(models.Model):
    """Модель полученного пользователем значка"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_('пользователь')
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='user_badges',
        verbose_name=_('значок')
    )
    earned_at = models.DateTimeField(_('получено'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('значок пользователя')
        verbose_name_plural = _('значки пользователей')
        unique_together = ['user', 'badge']
        ordering = ['-earned_at'] 