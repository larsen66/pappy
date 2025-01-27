from django.db import models
from django.conf import settings

class DialogManager(models.Manager):
    def get_or_create_for_users(self, user1, user2, announcement=None):
        """
        Получает или создает диалог между двумя пользователями
        """
        dialog = self.filter(participants=user1).filter(participants=user2).first()
        if dialog:
            return dialog, False
        
        dialog = self.create(announcement=announcement)
        dialog.participants.add(user1, user2)
        return dialog, True

class Dialog(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='dialogs',
        verbose_name='Участники'
    )
    announcement = models.ForeignKey(
        'announcements.Announcement',
        on_delete=models.CASCADE,
        related_name='dialogs',
        verbose_name='Объявление',
        null=True,
        blank=True
    )
    created = models.DateTimeField(
        'Создан',
        auto_now_add=True
    )
    updated = models.DateTimeField(
        'Обновлен',
        auto_now=True
    )
    
    objects = DialogManager()
    
    class Meta:
        ordering = ['-updated']
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
    
    def __str__(self):
        participants = self.participants.all()
        if participants.count() >= 2:
            return f'Диалог между {participants[0]} и {participants[1]}'
        return f'Диалог {self.id}'
    
    def get_absolute_url(self):
        return f'/chat/{self.id}/'

class Chat(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chats',
        verbose_name='Участники'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        ordering = ['-updated_at']

    def __str__(self):
        return f'Чат {self.id}'

class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель'
    )
    text = models.TextField('Текст сообщения')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Отправлено'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'Сообщение от {self.sender} в чате {self.chat.id}' 