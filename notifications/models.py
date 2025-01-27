from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class NotificationPreference(models.Model):
    """Настройки уведомлений пользователя"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email уведомления
    email_new_matches = models.BooleanField(_('Новые совпадения'), default=True)
    email_new_messages = models.BooleanField(_('Новые сообщения'), default=True)
    email_status_updates = models.BooleanField(_('Обновления статуса'), default=True)
    email_recommendations = models.BooleanField(_('Новые рекомендации'), default=True)
    email_lost_pets = models.BooleanField(_('Потерянные животные'), default=True)
    
    # Push уведомления
    push_new_matches = models.BooleanField(_('Новые совпадения'), default=True)
    push_new_messages = models.BooleanField(_('Новые сообщения'), default=True)
    push_status_updates = models.BooleanField(_('Обновления статуса'), default=True)
    push_recommendations = models.BooleanField(_('Новые рекомендации'), default=True)
    push_lost_pets = models.BooleanField(_('Потерянные животные'), default=True)
    
    # Настройки частоты
    email_frequency = models.CharField(
        _('Частота email уведомлений'),
        max_length=20,
        choices=[
            ('instant', _('Мгновенно')),
            ('daily', _('Раз в день')),
            ('weekly', _('Раз в неделю')),
        ],
        default='instant'
    )
    
    quiet_hours_start = models.TimeField(
        _('Начало тихого времени'),
        null=True,
        blank=True
    )
    quiet_hours_end = models.TimeField(
        _('Конец тихого времени'),
        null=True,
        blank=True
    )
    
    # Геолокация для уведомлений о потерянных животных
    lost_pets_radius = models.PositiveIntegerField(
        _('Радиус уведомлений о потеряшках (км)'),
        default=10
    )
    
    class Meta:
        verbose_name = _('Настройки уведомлений')
        verbose_name_plural = _('Настройки уведомлений')

class Notification(models.Model):
    """Модель уведомления"""
    NOTIFICATION_TYPES = [
        ('match', _('Новое совпадение')),
        ('message', _('Новое сообщение')),
        ('status_update', _('Обновление статуса')),
        ('recommendation', _('Рекомендация')),
        ('lost_pet', _('Потерянное животное')),
        ('system', _('Системное уведомление')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        _('Тип уведомления'),
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(_('Заголовок'), max_length=255)
    message = models.TextField(_('Сообщение'))
    
    # Связь с объектом уведомления (например, объявление или сообщение)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Метаданные
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    read_at = models.DateTimeField(_('Прочитано'), null=True, blank=True)
    is_read = models.BooleanField(_('Прочитано'), default=False)
    
    # Статус отправки
    is_email_sent = models.BooleanField(_('Email отправлен'), default=False)
    is_push_sent = models.BooleanField(_('Push отправлен'), default=False)
    
    class Meta:
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} для {self.user}"
    
    def mark_as_read(self):
        """Отметить уведомление как прочитанное"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

class NotificationBatch(models.Model):
    """Модель для группировки уведомлений для отложенной отправки"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_batches'
    )
    notifications = models.ManyToManyField(
        Notification,
        related_name='batch'
    )
    frequency = models.CharField(
        _('Частота отправки'),
        max_length=20,
        choices=[
            ('daily', _('Ежедневно')),
            ('weekly', _('Еженедельно')),
        ]
    )
    scheduled_at = models.DateTimeField(_('Запланировано на'))
    sent_at = models.DateTimeField(_('Отправлено'), null=True, blank=True)
    is_sent = models.BooleanField(_('Отправлено'), default=False)
    
    class Meta:
        verbose_name = _('Пакет уведомлений')
        verbose_name_plural = _('Пакеты уведомлений')
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['user', 'scheduled_at']),
            models.Index(fields=['is_sent']),
        ]

class PushToken(models.Model):
    """Модель для хранения push-токенов устройств"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_tokens'
    )
    token = models.CharField(_('Push-токен'), max_length=255)
    device_type = models.CharField(
        _('Тип устройства'),
        max_length=20,
        choices=[
            ('ios', 'iOS'),
            ('android', 'Android'),
            ('web', 'Web'),
        ]
    )
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    last_used_at = models.DateTimeField(
        _('Последнее использование'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Push-токен')
        verbose_name_plural = _('Push-токены')
        unique_together = ('user', 'token')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f'{self.user} - {self.token}' 