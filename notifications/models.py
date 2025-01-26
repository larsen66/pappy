from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPES = (
        ('message', 'Новое сообщение'),
        ('profile', 'Обновление профиля'),
        ('system', 'Системное уведомление'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=TYPES,
        verbose_name='Тип уведомления'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок'
    )
    message = models.TextField(
        verbose_name='Сообщение'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_notification_type_display()} для {self.user}'
    
    @classmethod
    def create_message_notification(cls, user, chat):
        """Создает уведомление о новом сообщении"""
        last_message = chat.messages.last()
        if last_message and last_message.sender != user:
            return cls.objects.create(
                user=user,
                notification_type='message',
                title='Новое сообщение',
                message=f'Новое сообщение от {last_message.sender}'
            )
    
    @classmethod
    def create_profile_notification(cls, user, action):
        """Создает уведомление об изменении профиля"""
        return cls.objects.create(
            user=user,
            notification_type='profile',
            title='Профиль обновлен',
            message=f'Ваш профиль был {action}'
        )
    
    @classmethod
    def create_system_notification(cls, user, title, message):
        """Создает системное уведомление"""
        return cls.objects.create(
            user=user,
            notification_type='system',
            title=title,
            message=message
        )
    
    @classmethod
    def create_match_notification(cls, recipient, product):
        """Создает уведомление о взаимном лайке"""
        return cls.objects.create(
            recipient=recipient,
            type='match',
            title='Новый матч!',
            text=f'Взаимный интерес к объявлению "{product.title}"',
            link=f'/chat/create/{product.id}/'
        )
    
    @classmethod
    def create_product_status_notification(cls, recipient, product, status):
        """Создает уведомление об изменении статуса объявления"""
        status_choices = {
            'active': 'активный',
            'archived': 'в архиве',
            'draft': 'черновик',
            'moderation': 'на модерации',
            'rejected': 'отклонен'
        }
        status_display = status_choices.get(status, status)
        return cls.objects.create(
            recipient=recipient,
            type='product_status',
            title='Статус объявления изменен',
            text=f'Статус вашего объявления "{product.title}" изменен на "{status_display}"',
            link=f'/catalog/product/{product.slug}/'
        )
    
    @classmethod
    def create_verification_notification(cls, recipient, is_verified):
        """Создает уведомление о результате верификации"""
        status = 'подтвержден' if is_verified else 'отклонен'
        return cls.objects.create(
            recipient=recipient,
            type='verification',
            title='Результат верификации',
            text=f'Ваш аккаунт {status}',
            link='/profile/verification/'
        )
    
    @classmethod
    def create_lost_pet_notification(cls, recipient, product):
        """Создает уведомление о потерянном питомце поблизости"""
        return cls.objects.create(
            recipient=recipient,
            type='lost_pet_nearby',
            title='Потерянный питомец рядом',
            text=f'В вашем районе пропал питомец: {product.title}. Местоположение: {product.location}',
            link=f'/catalog/product/{product.slug}/'
        ) 