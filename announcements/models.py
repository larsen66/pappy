from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from unidecode import unidecode
from django.core.exceptions import ValidationError
from django.utils import timezone
import json

class AnnouncementCategory(models.Model):
    name = models.CharField(_('Название'), max_length=100)
    slug = models.SlugField(_('Слаг'), unique=True)
    description = models.TextField(_('Описание'), blank=True)
    parent = models.ForeignKey('self', verbose_name=_('Родительская категория'),
                             on_delete=models.CASCADE, null=True, blank=True,
                             related_name='children')
    
    class Meta:
        verbose_name = _('Категория объявления')
        verbose_name_plural = _('Категории объявлений')
        ordering = ['name']

    def __str__(self):
        return self.name

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
    is_active = models.BooleanField(_('Активно'), default=True)
    
    # Геолокация
    address = models.CharField(_('адрес'), max_length=255, null=True, blank=True)
    latitude = models.DecimalField(_('широта'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('долгота'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Изображения
    images = models.TextField(_('Изображения'), default='[]')  # JSON строка для хранения списка URL изображений
    
    class Meta:
        verbose_name = _('Объявление')
        verbose_name_plural = _('Объявления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.title

    def get_images(self):
        return json.loads(self.images)

    def set_images(self, images_list):
        self.images = json.dumps(images_list)

    def clean(self):
        if self.latitude and not self.longitude:
            raise ValidationError(_('Необходимо указать обе координаты'))
        if self.longitude and not self.latitude:
            raise ValidationError(_('Необходимо указать обе координаты'))

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

    announcement = models.OneToOneField(
        Announcement,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='animal_details'
    )
    
    # Характеристики животного
    species = models.CharField(_('Вид животного'), max_length=100)
    breed = models.CharField(_('Порода'), max_length=100, blank=True)
    age = models.PositiveIntegerField(_('Возраст'), null=True, blank=True)
    gender = models.CharField(_('Пол'), max_length=10, choices=GENDER_CHOICES)
    size = models.CharField(_('Размер'), max_length=20, choices=SIZE_CHOICES)
    color = models.CharField(_('Окрас'), max_length=50)
    
    # Дополнительные характеристики
    pedigree = models.BooleanField(_('Родословная'), default=False)
    vaccinated = models.BooleanField(_('Вакцинирован'), default=False)
    passport = models.BooleanField(_('Ветеринарный паспорт'), default=False)
    microchipped = models.BooleanField(_('Чипирован'), default=False)
    
    class Meta:
        verbose_name = _('Объявление о животном')
        verbose_name_plural = _('Объявления о животных')

    def __str__(self):
        return f"{self.species} - {self.announcement.title}"

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
    
    # Характеристики животного
    animal = models.ForeignKey(AnimalAnnouncement, verbose_name=_('Животное'),
                             on_delete=models.CASCADE, related_name='mating_profiles',
                             null=True, blank=True)
    
    # Медицинские документы
    has_medical_exam = models.BooleanField(_('Пройден медосмотр'), default=False)
    medical_exam_date = models.DateField(_('Дата медосмотра'), null=True, blank=True)
    vaccinations = models.JSONField(_('Прививки'), null=True, blank=True)
    genetic_tests = models.JSONField(_('Генетические тесты'), null=True, blank=True)
    medical_documents = models.FileField(_('Медицинские документы'), upload_to='mating/medical_docs/', null=True, blank=True)
    
    # Достижения и титулы
    titles = models.TextField(_('Титулы'), default='[]')  # JSON строка для хранения списка титулов
    achievements = models.TextField(_('Достижения'), blank=True)
    show_participation = models.JSONField(_('Участие в выставках'), null=True, blank=True)
    
    # Требования к партнеру
    partner_requirements = models.TextField(_('Требования к партнеру'), null=True, blank=True)
    preferred_breeds = models.TextField(_('Предпочтительные породы'), default='[]')  # JSON строка для хранения списка пород
    min_partner_age = models.PositiveIntegerField(_('Минимальный возраст партнера'), null=True, blank=True)
    max_partner_age = models.PositiveIntegerField(_('Максимальный возраст партнера'), null=True, blank=True)
    required_medical_tests = models.JSONField(_('Требуемые медицинские тесты'), null=True, blank=True)
    required_titles = models.JSONField(_('Требуемые титулы'), null=True, blank=True)
    
    # Условия вязки
    mating_conditions = models.TextField(_('Условия вязки'), null=True, blank=True)
    price_policy = models.CharField(_('Ценовая политика'), max_length=100, null=True, blank=True)
    contract_required = models.BooleanField(_('Требуется контракт'), default=True)
    
    # Статистика и метаданные
    successful_matings = models.PositiveIntegerField(_('Успешные вязки'), default=0)
    last_mating_date = models.DateField(_('Дата последней вязки'), null=True, blank=True)
    is_available = models.BooleanField(_('Доступен для вязки'), default=True)
    
    class Meta:
        verbose_name = _('Объявление о вязке')
        verbose_name_plural = _('Объявления о вязке')
        indexes = [
            models.Index(fields=['is_available']),
            models.Index(fields=['successful_matings']),
        ]
    
    def __str__(self):
        return f"Вязка: {self.animal.breed if self.animal else 'Без животного'} ({self.animal.gender if self.animal else '-'})"
    
    def clean(self):
        super().clean()
        if self.animal:
            if self.animal.gender not in [AnimalAnnouncement.GENDER_MALE, AnimalAnnouncement.GENDER_FEMALE]:
                raise ValidationError(_('Необходимо указать пол животного'))
            
            if self.medical_exam_date and self.medical_exam_date > timezone.now().date():
                raise ValidationError(_('Дата медосмотра не может быть в будущем'))
    
    def get_titles(self):
        return json.loads(self.titles)
    
    def set_titles(self, titles_list):
        self.titles = json.dumps(titles_list)
    
    def get_preferred_breeds(self):
        return json.loads(self.preferred_breeds)
    
    def set_preferred_breeds(self, breeds_list):
        self.preferred_breeds = json.dumps(breeds_list)

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
    animal_type = models.CharField(
        _('Тип животного'),
        max_length=20,
        choices=ANIMAL_TYPE_CHOICES,
        null=True,
        blank=True
    )
    breed = models.CharField(_('Порода'), max_length=100, blank=True)
    color = models.CharField(
        _('Основной цвет'),
        max_length=50,
        null=True,
        blank=True
    )
    size = models.CharField(_('Размер'), max_length=20, choices=SIZE_CHOICES, default='medium')
    distinctive_features = models.TextField(_('Отличительные черты'))
    
    # Location fields
    date_lost_found = models.DateTimeField(_('Дата и время пропажи/находки'))
    location = models.CharField(_('Место пропажи/находки'), max_length=255, null=True, blank=True, default='')
    latitude = models.DecimalField(_('Широта'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Долгота'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact information
    contact_phone = models.CharField(
        _('Контактный телефон'),
        max_length=20,
        null=True,
        blank=True
    )
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    reward_amount = models.DecimalField(
        _('Сумма вознаграждения'), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Additional features
    color_pattern = models.CharField(_('Тип окраса'), max_length=50, blank=True)
    microchipped = models.BooleanField(_('Есть микрочип'), default=False)
    collar_details = models.CharField(_('Детали ошейника'), max_length=255, blank=True)
    special_marks = models.JSONField(_('Особые приметы'), null=True, blank=True)
    
    # Search history tracking
    search_history = models.JSONField(_('История поиска'), null=True, blank=True)
    search_areas = models.JSONField(_('Зоны поиска'), null=True, blank=True)
    contacted_users = models.TextField(_('Контактированные пользователи'), default='[]')  # JSON строка для хранения списка пользователей
    
    class Meta:
        verbose_name = _('Объявление о потере/находке')
        verbose_name_plural = _('Объявления о потере/находке')
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['animal_type']),
            models.Index(fields=['date_lost_found']),
        ]
    
    def get_contacted_users(self):
        return json.loads(self.contacted_users)
    
    def set_contacted_users(self, users_list):
        self.contacted_users = json.dumps(users_list)

class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(Announcement, verbose_name=_('Объявление'),
                                   on_delete=models.CASCADE, related_name='announcement_images')
    image = models.ImageField(_('Изображение'), upload_to='announcements/')
    is_main = models.BooleanField(_('Главное изображение'), default=False)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Изображение объявления')
        verbose_name_plural = _('Изображения объявлений')
        ordering = ['-is_main', '-created_at']

class LostPet(models.Model):
    STATUS_LOST = 'lost'
    STATUS_FOUND = 'found'
    STATUS_RESOLVED = 'resolved'
    
    STATUS_CHOICES = [
        (STATUS_LOST, _('Потерян')),
        (STATUS_FOUND, _('Найден')),
        (STATUS_RESOLVED, _('Разрешено')),
    ]
    
    # Основная информация
    announcement = models.OneToOneField('Announcement', on_delete=models.CASCADE, related_name='lost_pet')
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default=STATUS_LOST)
    date_lost_found = models.DateTimeField(_('Дата пропажи/находки'))
    
    # Характеристики животного
    pet_type = models.CharField(_('Вид животного'), max_length=50)
    breed = models.CharField(_('Порода'), max_length=100, blank=True)
    color = models.CharField(_('Цвет'), max_length=50)
    age = models.IntegerField(_('Примерный возраст'), null=True, blank=True)
    distinctive_features = models.TextField(_('Отличительные черты'))
    has_collar = models.BooleanField(_('Есть ошейник'), default=False)
    has_chip = models.BooleanField(_('Есть чип'), default=False)
    chip_number = models.CharField(_('Номер чипа'), max_length=50, blank=True)
    
    # Геолокация
    last_seen_location = models.CharField(_('Место последней встречи'), max_length=255)
    last_seen_latitude = models.DecimalField(_('Широта последней встречи'), max_digits=9, decimal_places=6, null=True, blank=True)
    last_seen_longitude = models.DecimalField(_('Долгота последней встречи'), max_digits=9, decimal_places=6, null=True, blank=True)
    search_radius = models.IntegerField(_('Радиус поиска (км)'), default=5)
    
    # Контактная информация
    contact_name = models.CharField(_('Контактное лицо'), max_length=100)
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    reward_offered = models.DecimalField(_('Вознаграждение'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    is_active = models.BooleanField(_('Активно'), default=True)
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    
    class Meta:
        verbose_name = _('Потерянное животное')
        verbose_name_plural = _('Потерянные животные')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['date_lost_found']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.pet_type} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Обновляем дату изменения объявления
        self.announcement.save()
        super().save(*args, **kwargs)
    
    @property
    def location_coordinates(self):
        if self.last_seen_latitude and self.last_seen_longitude:
            return {
                'latitude': self.last_seen_latitude,
                'longitude': self.last_seen_longitude
            }
        return None
