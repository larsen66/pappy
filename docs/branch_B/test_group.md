# Документация по тестам выполненных задач

## 1. Тесты потеряшек (`announcements/tests/test_lost_pets.py`)
Тестирует следующие задачи из раздела "3. Потеряшки":

### ✓ Геолокация места пропажи
```python
# Из completed_tasks.md:
class Announcement(models.Model):
    location = models.CharField(_('Местоположение'), max_length=200)
    latitude = models.DecimalField(_('широта'), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_('долгота'), max_digits=9, decimal_places=6)
```

### ✓ Быстрые фильтры
```python
# Из completed_tasks.md:
class LostFoundAnnouncement(models.Model):
    TYPE_CHOICES = [
        (TYPE_LOST, _('Потеряно')),
        (TYPE_FOUND, _('Найдено')),
    ]
```

## 2. Тесты уведомлений (`announcements/tests/test_notifications.py`)
Тестирует следующие задачи из раздела "3.2 Поиск совпадений":

### ✓ Автоматические уведомления
```python
# Из completed_tasks.md:
class NotificationConsumer(WebsocketConsumer):
    def send_notification(self, event):
        self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))
```

### ✓ Система уведомлений
```python
# Из completed_tasks.md:
class NotificationService:
    @staticmethod
    def notify_users_in_radius(announcement, radius_km: int)
```

## 3. Тесты чат-системы (`chat/tests/test_views.py`)
Тестирует следующие задачи из раздела "2. Чат-система":

### ✓ Диалоги и сообщения
```python
# Из completed_tasks.md:
class Dialog(models.Model):
    participants = models.ManyToManyField(User)
    last_message = models.ForeignKey('Message', null=True)
```

### ✓ Статусы сообщений
```python
# Из completed_tasks.md:
class Message(models.Model):
    is_read = models.BooleanField(default=False)
```

## 4. Тесты VIP функционала (`user_profile/tests/test_vip.py`)
Тестирует следующие задачи из раздела "2. VIP-функционал":

### ✓ Модели подписок и уровней
```python
# Из completed_tasks.md:
class VIPSubscription(models.Model):
    LEVEL_CHOICES = [
        ('basic', 'Базовый'),
        ('premium', 'Премиум'),
        ('elite', 'Элитный'),
    ]
``` 