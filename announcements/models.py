from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from unidecode import unidecode
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.contrib.gis.geos import Distance
from django.core.exceptions import ValidationError

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
    
    # Характеристики животного
    animal = models.OneToOneField(AnimalAnnouncement, verbose_name=_('Животное'),
                                on_delete=models.CASCADE, related_name='mating_profile')
    
    # Медицинские документы
    has_medical_exam = models.BooleanField(_('Пройден медосмотр'), default=False)
    medical_exam_date = models.DateField(_('Дата медосмотра'), null=True, blank=True)
    vaccinations = models.JSONField(_('Прививки'), null=True, blank=True)
    genetic_tests = models.JSONField(_('Генетические тесты'), null=True, blank=True)
    medical_documents = models.FileField(_('Медицинские документы'), upload_to='mating/medical_docs/', null=True, blank=True)
    
    # Достижения и титулы
    titles = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_('Титулы'),
        null=True, blank=True
    )
    achievements = models.TextField(_('Достижения'), blank=True)
    show_participation = models.JSONField(_('Участие в выставках'), null=True, blank=True)
    
    # Требования к партнеру
    partner_requirements = models.TextField(_('Требования к партнеру'))
    preferred_breeds = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_('Предпочтительные породы'),
        null=True, blank=True
    )
    min_partner_age = models.PositiveIntegerField(_('Минимальный возраст партнера'), null=True, blank=True)
    max_partner_age = models.PositiveIntegerField(_('Максимальный возраст партнера'), null=True, blank=True)
    required_medical_tests = models.JSONField(_('Требуемые медицинские тесты'), null=True, blank=True)
    required_titles = models.JSONField(_('Требуемые титулы'), null=True, blank=True)
    
    # Условия вязки
    mating_conditions = models.TextField(_('Условия вязки'))
    price_policy = models.CharField(_('Ценовая политика'), max_length=100)
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
        return f"Вязка: {self.animal.breed} ({self.animal.gender})"
    
    def clean(self):
        super().clean()
        if self.animal.gender not in [AnimalAnnouncement.GENDER_MALE, AnimalAnnouncement.GENDER_FEMALE]:
            raise ValidationError(_('Необходимо указать пол животного'))
        
        if self.medical_exam_date and self.medical_exam_date > timezone.now().date():
            raise ValidationError(_('Дата медосмотра не может быть в будущем'))
    
    def get_matching_partners(self):
        """Поиск подходящих партнеров для вязки"""
        base_query = MatingAnnouncement.objects.filter(
            is_available=True,
            animal__species=self.animal.species,
            animal__gender=AnimalAnnouncement.GENDER_MALE if self.animal.gender == AnimalAnnouncement.GENDER_FEMALE else AnimalAnnouncement.GENDER_FEMALE
        ).exclude(id=self.id)
        
        if self.preferred_breeds:
            base_query = base_query.filter(animal__breed__in=self.preferred_breeds)
        
        if self.min_partner_age:
            base_query = base_query.filter(animal__age__gte=self.min_partner_age)
        
        if self.max_partner_age:
            base_query = base_query.filter(animal__age__lte=self.max_partner_age)
        
        return base_query

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
    size = models.CharField(_('Размер'), max_length=20, choices=SIZE_CHOICES)
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
    last_seen_location = gis_models.PointField(_('Место последней встречи'))
    last_seen_address = models.CharField(_('Адрес последней встречи'), max_length=255)
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
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['pet_type', 'breed']),
            models.Index(fields=['date_lost_found']),
        ]
    
    def __str__(self):
        return f"{self.get_status_display()} {self.pet_type} - {self.last_seen_address}"
    
    def save(self, *args, **kwargs):
        # Обновляем дату изменения объявления
        self.announcement.updated_at = timezone.now()
        self.announcement.save()
        super().save(*args, **kwargs)
    
    @property
    def location_coordinates(self):
        return {
            'latitude': self.last_seen_location.y,
            'longitude': self.last_seen_location.x
        }
    
    def get_similar_cases(self, radius_km=None):
        """Поиск похожих случаев в заданном радиусе"""
        if radius_km is None:
            radius_km = self.search_radius
        
        return LostPet.objects.filter(
            is_active=True,
            last_seen_location__distance_lte=(
                self.last_seen_location,
                Distance(km=radius_km)
            ),
            pet_type=self.pet_type,
            status__in=['lost', 'found']
        ).exclude(id=self.id)
