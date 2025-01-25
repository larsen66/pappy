from django.db import models
from django.conf import settings

class DialogManager(models.Manager):
    def get_or_create_for_users(self, user1, user2, product=None):
        """
        Получает или создает диалог между двумя пользователями
        """
        dialog = self.filter(participants=user1).filter(participants=user2).first()
        if dialog:
            return dialog, False
        
        dialog = self.create(product=product)
        dialog.participants.add(user1, user2)
        return dialog, True

class Dialog(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='dialogs',
        verbose_name='Участники'
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='dialogs',
        verbose_name='Продукт',
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

class Message(models.Model):
    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Диалог'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель'
    )
    text = models.TextField('Текст')
    created = models.DateTimeField(
        'Создано',
        auto_now_add=True
    )
    is_read = models.BooleanField(
        'Прочитано',
        default=False
    )
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created']
    
    def __str__(self):
        return f'Сообщение от {self.sender} в {self.dialog}' 