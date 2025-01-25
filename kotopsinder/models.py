from django.db import models
from django.conf import settings
from catalog.models import Product
from chat.models import Dialog

class Swipe(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    DIRECTION_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='swipes')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='swipes')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} {self.direction}d {self.product}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Если это лайк, создаем диалог между пользователями
        if self.direction == self.LIKE:
            dialog, created = Dialog.objects.get_or_create_for_users(
                self.user,
                self.product.seller,
                product=self.product
            )

class SwipeHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='swipe_history')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='swipe_history')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']
        verbose_name = 'История свайпов'
        verbose_name_plural = 'Истории свайпов'

    def __str__(self):
        return f"{self.user} viewed {self.product}" 