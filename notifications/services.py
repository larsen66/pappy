from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from datetime import timedelta
import firebase_admin
from firebase_admin import messaging
from .models import (
    Notification,
    NotificationPreference,
    NotificationBatch,
    PushToken
)

class NotificationService:
    """Сервис для работы с уведомлениями"""
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, content_object=None):
        """Создание нового уведомления"""
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            content_type=ContentType.objects.get_for_model(content_object) if content_object else None,
            object_id=content_object.id if content_object else None
        )
        
        # Получаем настройки пользователя
        preferences = NotificationPreference.objects.get_or_create(user=user)[0]
        
        # Проверяем время для тихого режима
        current_time = timezone.localtime().time()
        is_quiet_time = False
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            if preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end:
                is_quiet_time = True
        
        # Отправляем уведомления в зависимости от настроек
        if not is_quiet_time:
            # Email уведомления
            if cls._should_send_email(preferences, notification_type):
                if preferences.email_frequency == 'instant':
                    cls._send_email_notification(notification)
                else:
                    cls._add_to_batch(notification, preferences.email_frequency)
            
            # Push уведомления
            if cls._should_send_push(preferences, notification_type):
                cls._send_push_notification(notification)
        
        return notification
    
    @staticmethod
    def _should_send_email(preferences, notification_type):
        """Проверка необходимости отправки email"""
        mapping = {
            'match': preferences.email_new_matches,
            'message': preferences.email_new_messages,
            'status_update': preferences.email_status_updates,
            'recommendation': preferences.email_recommendations,
            'lost_pet': preferences.email_lost_pets,
        }
        return mapping.get(notification_type, True)
    
    @staticmethod
    def _should_send_push(preferences, notification_type):
        """Проверка необходимости отправки push"""
        mapping = {
            'match': preferences.push_new_matches,
            'message': preferences.push_new_messages,
            'status_update': preferences.push_status_updates,
            'recommendation': preferences.push_recommendations,
            'lost_pet': preferences.push_lost_pets,
        }
        return mapping.get(notification_type, True)
    
    @staticmethod
    def _send_email_notification(notification):
        """Отправка email уведомления"""
        context = {
            'notification': notification,
            'user': notification.user,
        }
        
        html_content = render_to_string('notifications/email/notification.html', context)
        text_content = render_to_string('notifications/email/notification.txt', context)
        
        send_mail(
            subject=notification.title,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            html_message=html_content
        )
        
        notification.is_email_sent = True
        notification.save()
    
    @staticmethod
    def _send_push_notification(notification):
        """Отправка push уведомления"""
        tokens = PushToken.objects.filter(
            user=notification.user,
            is_active=True
        ).values_list('token', flat=True)
        
        if not tokens:
            return
        
        message = messaging.MulticastMessage(
            tokens=list(tokens),
            notification=messaging.Notification(
                title=notification.title,
                body=notification.message,
            ),
            data={
                'notification_id': str(notification.id),
                'type': notification.notification_type,
                'content_type': str(notification.content_type.id) if notification.content_type else '',
                'object_id': str(notification.object_id) if notification.object_id else '',
            }
        )
        
        try:
            response = messaging.send_multicast(message)
            # Обновляем статус токенов
            for idx, result in enumerate(response.responses):
                if not result.success:
                    PushToken.objects.filter(token=tokens[idx]).update(is_active=False)
            
            notification.is_push_sent = True
            notification.save()
        except Exception as e:
            print(f"Error sending push notification: {e}")
    
    @staticmethod
    def _add_to_batch(notification, frequency):
        """Добавление уведомления в пакет для отложенной отправки"""
        now = timezone.now()
        
        if frequency == 'daily':
            # Планируем на следующий день в 9:00
            next_run = (now + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
        else:  # weekly
            # Планируем на следующий понедельник в 9:00
            days_ahead = 7 - now.weekday()
            next_run = (now + timedelta(days=days_ahead)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
        
        batch, created = NotificationBatch.objects.get_or_create(
            user=notification.user,
            frequency=frequency,
            scheduled_at=next_run,
            is_sent=False
        )
        batch.notifications.add(notification)
    
    @classmethod
    def process_batches(cls):
        """Обработка отложенных уведомлений"""
        now = timezone.now()
        batches = NotificationBatch.objects.filter(
            scheduled_at__lte=now,
            is_sent=False
        ).select_related('user').prefetch_related('notifications')
        
        for batch in batches:
            notifications = batch.notifications.all()
            if not notifications:
                continue
            
            # Группируем уведомления по типу
            notifications_by_type = {}
            for notification in notifications:
                if notification.notification_type not in notifications_by_type:
                    notifications_by_type[notification.notification_type] = []
                notifications_by_type[notification.notification_type].append(notification)
            
            # Отправляем сгруппированное email уведомление
            context = {
                'user': batch.user,
                'notifications_by_type': notifications_by_type,
                'frequency': batch.frequency,
            }
            
            html_content = render_to_string('notifications/email/batch.html', context)
            text_content = render_to_string('notifications/email/batch.txt', context)
            
            send_mail(
                subject=f"Уведомления за {'день' if batch.frequency == 'daily' else 'неделю'}",
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[batch.user.email],
                html_message=html_content
            )
            
            # Обновляем статус уведомлений и пакета
            notifications.update(is_email_sent=True)
            batch.is_sent = True
            batch.sent_at = now
            batch.save()
    
    @staticmethod
    def mark_as_read(user, notification_ids=None):
        """Отметить уведомления как прочитанные"""
        now = timezone.now()
        queryset = Notification.objects.filter(user=user, is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        queryset.update(is_read=True, read_at=now)
    
    @staticmethod
    def get_unread_count(user):
        """Получить количество непрочитанных уведомлений"""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def register_push_token(user, token, device_type):
        """Регистрация нового push-токена"""
        token_obj, created = PushToken.objects.get_or_create(
            user=user,
            token=token,
            defaults={'device_type': device_type}
        )
        
        if not created:
            token_obj.is_active = True
            token_obj.last_used_at = timezone.now()
            token_obj.save()
        
        return token_obj
    
    @staticmethod
    def unregister_push_token(user, token):
        """Отключение push-токена"""
        PushToken.objects.filter(user=user, token=token).update(is_active=False) 