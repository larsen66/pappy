from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from unidecode import unidecode
from django.contrib.postgres.fields import ArrayField

class AnnouncementCategory(models.Model):
    name = models.CharField(_('Название'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True)
    parent = models.ForeignKey('self', verbose_name=_('Родительская категория'),
                             on_delete=models.CASCADE, null=True, blank=True,
                             related_name='children')
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['name']
        
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

class Announcement(models.Model):
    TYPE_ANIMAL = 'animal'
    TYPE_SERVICE = 'service'
    TYPE_MATING = 'mating'
    TYPE_LOST_FOUND = 'lost_found'
    
    ANNOUNCEMENT_TYPE_CHOICES = [
        (TYPE_ANIMAL, _('Животное')),
        (TYPE_SERVICE, _('Услуга')),
        (TYPE_MATING, _('Вязка')),
        (TYPE_LOST_FOUND, _('Потеряно/Найдено')),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_MODERATION = 'moderation'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Активно')),
        (STATUS_CLOSED, _('Закрыто')),
        (STATUS_MODERATION, _('На модерации')),
    ]

    # Основные поля
    title = models.CharField(_('Заголовок'), max_length=200)
    description = models.TextField(_('Описание'))
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(AnnouncementCategory, verbose_name=_('Категория'),
                               on_delete=models.CASCADE, related_name='announcements')
    type = models.CharField(_('Тип'), max_length=20, choices=ANNOUNCEMENT_TYPE_CHOICES)
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default=STATUS_MODERATION)
    
    # Связи
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Автор'),
                             on_delete=models.CASCADE, related_name='announcements')
    
    # Метаданные
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    views_count = models.PositiveIntegerField(_('Просмотры'), default=0)
    is_premium = models.BooleanField(_('Премиум'), default=False)
    
    # Геолокация
    location = models.CharField(_('Местоположение'), max_length=200, null=True, blank=True)
    latitude = models.DecimalField(_('широта'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('долгота'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Объявление')
        verbose_name_plural = _('Объявления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return self.title

class AnimalAnnouncement(models.Model):
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    
    GENDER_CHOICES = [
        (GENDER_MALE, _('Мужской')),
        (GENDER_FEMALE, _('Женский')),
    ]

    SIZE_SMALL = 'small'
    SIZE_MEDIUM = 'medium'
    SIZE_LARGE = 'large'
    
    SIZE_CHOICES = [
        (SIZE_SMALL, _('Маленький')),
        (SIZE_MEDIUM, _('Средний')),
        (SIZE_LARGE, _('Большой')),
    ]

    announcement = models.OneToOneField(Announcement, verbose_name=_('Объявление'),
                                      on_delete=models.CASCADE, related_name='animal_details')
    
    # Характеристики животного
    species = models.CharField(_('Вид'), max_length=100)
    breed = models.CharField(_('Порода'), max_length=100, blank=True)
    age = models.PositiveIntegerField(_('Возраст'), null=True, blank=True)
    gender = models.CharField(_('Пол'), max_length=10, choices=GENDER_CHOICES)
    size = models.CharField(_('Размер'), max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(_('Окрас'), max_length=100)
    
    # Дополнительные характеристики
    pedigree = models.BooleanField(_('Родословная'), default=False)
    vaccinated = models.BooleanField(_('Вакцинирован'), default=False)
    passport = models.BooleanField(_('Ветеринарный паспорт'), default=False)
    microchipped = models.BooleanField(_('Чипирован'), default=False)
    
    class Meta:
        verbose_name = _('Объявление о животном')
        verbose_name_plural = _('Объявления о животных')

class ServiceAnnouncement(models.Model):
    SERVICE_TYPE_WALKING = 'walking'
    SERVICE_TYPE_GROOMING = 'grooming'
    SERVICE_TYPE_TRAINING = 'training'
    SERVICE_TYPE_VETERINARY = 'veterinary'
    SERVICE_TYPE_BOARDING = 'boarding'
    
    SERVICE_TYPE_CHOICES = [
        (SERVICE_TYPE_WALKING, _('Выгул')),
        (SERVICE_TYPE_GROOMING, _('Груминг')),
        (SERVICE_TYPE_TRAINING, _('Дрессировка')),
        (SERVICE_TYPE_VETERINARY, _('Ветеринарные услуги')),
        (SERVICE_TYPE_BOARDING, _('Передержка')),
    ]

    announcement = models.OneToOneField(Announcement, verbose_name=_('Объявление'),
                                      on_delete=models.CASCADE, related_name='service_details')
    
    service_type = models.CharField(_('Тип услуги'), max_length=20, choices=SERVICE_TYPE_CHOICES)
    experience = models.PositiveIntegerField(_('Опыт работы (лет)'))
    certificates = models.TextField(_('Сертификаты'), blank=True)
    schedule = models.TextField(_('График работы'))
    
    class Meta:
        verbose_name = _('Объявление об услуге')
        verbose_name_plural = _('Объявления об услугах')

class MatingAnnouncement(models.Model):
    announcement = models.OneToOneField(Announcement, verbose_name=_('Объявление'),
                                      on_delete=models.CASCADE, related_name='mating_details')
    
    requirements = models.TextField(_('Требования'))
    achievements = models.TextField(_('Достижения'), blank=True)
    
    class Meta:
        verbose_name = _('Объявление о вязке')
        verbose_name_plural = _('Объявления о вязке')

class LostFoundAnnouncement(models.Model):
    TYPE_LOST = 'lost'
    TYPE_FOUND = 'found'
    
    TYPE_CHOICES = [
        (TYPE_LOST, _('Потеряно')),
        (TYPE_FOUND, _('Найдено')),
    ]

    ANIMAL_TYPE_CHOICES = [
        ('dog', _('Собака')),
        ('cat', _('Кошка')),
        ('bird', _('Птица')),
        ('rodent', _('Грызун')),
        ('reptile', _('Рептилия')),
        ('fish', _('Рыба')),
        ('exotic', _('Экзотическое животное')),
    ]

    SIZE_CHOICES = [
        ('tiny', _('Очень маленький')),
        ('small', _('Маленький')),
        ('medium', _('Средний')),
        ('large', _('Большой')),
        ('very_large', _('Очень большой')),
    ]

    announcement = models.OneToOneField(
        Announcement, 
        verbose_name=_('Объявление'),
        on_delete=models.CASCADE, 
        related_name='lost_found_details'
    )
    
    type = models.CharField(_('Тип'), max_length=10, choices=TYPE_CHOICES)
    animal_type = models.CharField(_('Вид животного'), max_length=20, choices=ANIMAL_TYPE_CHOICES)
    breed = models.CharField(_('Порода'), max_length=100, blank=True)
    color = models.CharField(_('Основной цвет'), max_length=50)
    size = models.CharField(_('Размер'), max_length=20, choices=SIZE_CHOICES)
    distinctive_features = models.TextField(_('Отличительные черты'))
    
    # Location fields
    date_lost_found = models.DateTimeField(_('Дата и время пропажи/находки'))
    location = models.CharField(_('Место пропажи/находки'), max_length=255, null=True, blank=True, default='')
    latitude = models.DecimalField(_('Широта'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Долгота'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact information
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    reward_amount = models.DecimalField(
        _('Сумма вознаграждения'), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Additional features using PostgreSQL arrays and JSONB
    color_pattern = models.CharField(_('Тип окраса'), max_length=50, blank=True)
    microchipped = models.BooleanField(_('Есть микрочип'), default=False)
    collar_details = models.CharField(_('Детали ошейника'), max_length=255, blank=True)
    special_marks = models.JSONField(_('Особые приметы'), null=True, blank=True)
    
    # Search history tracking
    search_history = models.JSONField(_('История поиска'), null=True, blank=True)
    search_areas = models.JSONField(_('Зоны поиска'), null=True, blank=True)
    contacted_users = ArrayField(
        models.IntegerField(),
        verbose_name=_('Контакты с пользователями'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Объявление о потере/находке')
        verbose_name_plural = _('Объявления о потере/находке')
        indexes = [
            models.Index(fields=['type', 'animal_type']),
            models.Index(fields=['date_lost_found']),
            models.Index(fields=['location']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(Announcement, verbose_name=_('Объявление'),
                                   on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('Изображение'), upload_to='announcements/')
    is_main = models.BooleanField(_('Главное изображение'), default=False)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Изображение объявления')
        verbose_name_plural = _('Изображения объявлений')
        ordering = ['-is_main', '-created_at']
