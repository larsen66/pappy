from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from announcements.models import AnimalAnnouncement

class UserPreferences(models.Model):
    """Модель предпочтений пользователя для матчинга"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, 
                              on_delete=models.CASCADE,
                              related_name='matching_preferences')
    
    # Основные предпочтения
    preferred_species = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_('Предпочитаемые виды животных'),
        null=True, blank=True
    )
    preferred_breeds = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_('Предпочитаемые породы'),
        null=True, blank=True
    )
    preferred_age_min = models.PositiveIntegerField(_('Минимальный возраст'), null=True, blank=True)
    preferred_age_max = models.PositiveIntegerField(_('Максимальный возраст'), null=True, blank=True)
    preferred_gender = models.CharField(_('Предпочитаемый пол'), max_length=10, null=True, blank=True)
    
    # Дополнительные характеристики
    size_preference = ArrayField(
        models.CharField(max_length=20),
        verbose_name=_('Предпочитаемые размеры'),
        null=True, blank=True
    )
    color_preference = ArrayField(
        models.CharField(max_length=50),
        verbose_name=_('Предпочитаемые окрасы'),
        null=True, blank=True
    )
    
    # Специальные требования
    requires_pedigree = models.BooleanField(_('Требуется родословная'), default=False)
    requires_vaccinated = models.BooleanField(_('Требуется вакцинация'), default=True)
    requires_passport = models.BooleanField(_('Требуется ветпаспорт'), default=True)
    
    # Геолокация
    max_distance = models.PositiveIntegerField(
        _('Максимальное расстояние (км)'),
        default=50
    )
    
    # Метаданные
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    
    class Meta:
        verbose_name = _('Предпочтения пользователя')
        verbose_name_plural = _('Предпочтения пользователей')

class MatchingScore(models.Model):
    """Модель для хранения результатов матчинга"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='matching_scores')
    animal = models.ForeignKey(AnimalAnnouncement,
                             on_delete=models.CASCADE,
                             related_name='matching_scores')
    score = models.FloatField(_('Оценка совместимости'))
    matched_criteria = models.JSONField(_('Совпавшие критерии'))
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Оценка совместимости')
        verbose_name_plural = _('Оценки совместимости')
        unique_together = ('user', 'animal')
        indexes = [
            models.Index(fields=['-score']),
            models.Index(fields=['user', '-score']),
        ]

class UserInteraction(models.Model):
    """Модель для отслеживания взаимодействий пользователя"""
    INTERACTION_TYPES = [
        ('view', _('Просмотр')),
        ('like', _('Лайк')),
        ('dislike', _('Дизлайк')),
        ('favorite', _('В избранное')),
        ('contact', _('Контакт')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='animal_interactions')
    animal = models.ForeignKey(AnimalAnnouncement,
                             on_delete=models.CASCADE,
                             related_name='user_interactions')
    interaction_type = models.CharField(_('Тип взаимодействия'),
                                     max_length=20,
                                     choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Взаимодействие пользователя')
        verbose_name_plural = _('Взаимодействия пользователей')
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['animal', 'interaction_type']),
        ]

class RecommendationHistory(models.Model):
    """Модель для хранения истории рекомендаций"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='recommendation_history')
    animal = models.ForeignKey(AnimalAnnouncement,
                             on_delete=models.CASCADE,
                             related_name='recommendation_history')
    score = models.FloatField(_('Оценка рекомендации'))
    reason = models.JSONField(_('Причины рекомендации'))
    shown_at = models.DateTimeField(_('Показано'), auto_now_add=True)
    interacted = models.BooleanField(_('Было взаимодействие'), default=False)
    
    class Meta:
        verbose_name = _('История рекомендаций')
        verbose_name_plural = _('История рекомендаций')
        indexes = [
            models.Index(fields=['user', '-shown_at']),
            models.Index(fields=['-score']),
        ] 