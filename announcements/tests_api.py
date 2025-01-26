"""
Текущий статус (последнее обновление):

1. Тесты AnnouncementImageAPITests:
   - test_image_delete: возвращает 302 вместо 204
   - test_unauthorized_image_delete: возвращает 302 вместо 401
   
2. Настройки:
   - AnnouncementImageViewSet использует IsAuthenticated и IsAnnouncementAuthorOrReadOnly
   - URLs настроены через DefaultRouter с namespace 'api'
   - Аутентификация через TokenAuthentication
   
3. Текущая проблема:
   - Тесты получают редирект (302) вместо ожидаемых статусов
   - Возможные причины: middleware, конфигурация DRF, взаимодействие Django auth и DRF auth
   
4. Следующий шаг:
   - Разобраться с причиной редиректа
   - Исправить настройки аутентификации в тестовом окружении
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase as DRFAPITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    AnnouncementImage
)
from .serializers import (
    AnnouncementSerializer,
    AnimalAnnouncementSerializer,
    ServiceAnnouncementSerializer,
    AnnouncementImageSerializer
)
from rest_framework.authtoken.models import Token

User = get_user_model()

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'announcements.middleware.TestingModeMiddleware',
]

@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 12,
        'TEST_REQUEST_DEFAULT_FORMAT': 'json'
    }
)
class AnnouncementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.category = AnnouncementCategory.objects.create(
            name='Собаки',
            slug='dogs'
        )
        
        self.announcement_data = {
            'title': 'Test Announcement',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category.id,
            'type': 'animal',
            'location': 'Test City',
            'status': 'moderation'
        }
        
        self.announcement = Announcement.objects.create(
            author=self.user,
            category=self.category,
            title=self.announcement_data['title'],
            description=self.announcement_data['description'],
            price=self.announcement_data['price'],
            type=self.announcement_data['type'],
            location=self.announcement_data['location'],
            status=self.announcement_data['status']
        )

    def test_announcement_list(self):
        """Тест получения списка объявлений через API"""
        url = reverse('api:announcements-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_announcement_detail(self):
        """Тест получения деталей объявления через API"""
        url = reverse('api:announcements-detail', args=[self.announcement.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.announcement_data['title'])

    def test_announcement_create(self):
        """Тест создания объявления через API"""
        url = reverse('api:announcements-list')
        data = {
            'title': 'New Announcement',
            'description': 'New Description',
            'price': 2000,
            'category': self.category.id,
            'type': 'animal',
            'location': 'New City',
            'status': 'moderation'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Announcement.objects.count(), 2)

    def test_announcement_update(self):
        """Тест обновления объявления через API"""
        url = reverse('api:announcements-detail', args=[self.announcement.id])
        data = {
            'title': 'Updated Announcement',
            'description': 'Updated Description',
            'price': 3000,
            'category': self.category.id,
            'type': 'animal',
            'location': 'Updated City',
            'status': 'moderation'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title, 'Updated Announcement')

    def test_announcement_delete(self):
        """Тест удаления объявления через API"""
        url = reverse('api:announcements-detail', args=[self.announcement.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Announcement.objects.count(), 0)

    def test_unauthorized_access(self):
        """Тест доступа без авторизации"""
        self.client.credentials()  # Очищаем credentials
        url = reverse('api:announcements-list')
        response = self.client.post(url, self.announcement_data)  # Пытаемся создать объявление
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_announcement_filter(self):
        """Тест фильтрации объявлений через API"""
        url = reverse('api:announcements-list')
        response = self.client.get(url, {'type': 'animal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        response = self.client.get(url, {'type': 'service'})
        self.assertEqual(len(response.data['results']), 0)

    def test_announcement_search(self):
        """Тест поиска объявлений через API"""
        url = reverse('api:announcements-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        response = self.client.get(url, {'search': 'NonExistent'})
        self.assertEqual(len(response.data['results']), 0)

@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 12,
        'TEST_REQUEST_DEFAULT_FORMAT': 'json'
    }
)
class AnimalAnnouncementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.category = AnnouncementCategory.objects.create(
            name='Собаки',
            slug='dogs'
        )
        
        self.animal_data = {
            'title': 'Test Animal',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category,
            'type': 'animal',
            'location': 'Test City',
            'status': 'moderation',
            'species': 'dog',
            'breed': 'Labrador',
            'age': 2,
            'gender': 'male',
            'size': 'medium',
            'color': 'black',
            'vaccinated': True
        }

    def test_animal_announcement_create(self):
        """Тест создания объявления о животном через API"""
        url = reverse('api:animal-announcements-list')
        data = {
            'title': 'Dog Announcement',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category.id,
            'type': 'animal',
            'location': 'Test City',
            'status': 'moderation',
            'species': 'dog',
            'breed': 'Labrador',
            'age': 2,
            'gender': 'male',
            'size': 'medium',
            'color': 'black'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnimalAnnouncement.objects.count(), 1)
        self.assertEqual(AnimalAnnouncement.objects.first().species, 'dog')

    def test_animal_announcement_validation(self):
        """Тест валидации объявления о животном через API"""
        url = reverse('api:animal-announcements-list')
        data = {
            'title': 'Invalid Dog',
            'description': 'Test',
            'price': -100,  # Invalid price
            'category': self.category.id,
            'type': 'animal',
            'location': 'Test City'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 12,
        'TEST_REQUEST_DEFAULT_FORMAT': 'json'
    }
)
class ServiceAnnouncementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_specialist=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.category = AnnouncementCategory.objects.create(
            name='Услуги',
            slug='services'
        )
        
        self.service_data = {
            'title': 'Test Service',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category.id,
            'type': 'service',
            'location': 'Test City',
            'status': 'moderation',
            'service_type': 'grooming',
            'experience': 2,
            'schedule': 'Mon-Fri 9-18'
        }

    def test_service_announcement_create(self):
        """Тест создания объявления об услуге через API"""
        url = reverse('api:service-announcements-list')
        data = {
            'title': 'Dog Training',
            'description': 'Professional dog training',
            'price': 5000,
            'category': self.category.id,
            'type': 'service',
            'location': 'Test City',
            'status': 'moderation',
            'service_type': 'training',
            'experience': 5,
            'schedule': 'flexible'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceAnnouncement.objects.count(), 1)
        self.assertEqual(ServiceAnnouncement.objects.first().service_type, 'training')

    def test_service_announcement_specialist_required(self):
        """Тест создания объявления об услуге неспециалистом через API"""
        # Создаем обычного пользователя
        regular_user = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_specialist=False
        )
        self.client.force_authenticate(user=regular_user)
        
        url = reverse('api:service-announcements-list')
        response = self.client.post(url, self.service_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

@override_settings(
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
    },
    LOGIN_URL=None
)
class AnnouncementImageAPITests(DRFAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.category = AnnouncementCategory.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.announcement = Announcement.objects.create(
            title='Test Announcement',
            description='Test Description',
            author=self.user,
            category=self.category,
            price=1000,
            type='animal',
            location='Test City',
            status='moderation'
        )
        
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        
        self.announcement_image = AnnouncementImage.objects.create(
            announcement=self.announcement,
            image=self.image,
            is_main=True
        )

    def test_image_delete(self):
        """Тест удаления изображения через API"""
        initial_count = AnnouncementImage.objects.count()
        url = f'/api/images/{self.announcement_image.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AnnouncementImage.objects.count(), initial_count - 1)
        self.assertFalse(AnnouncementImage.objects.filter(id=self.announcement_image.id).exists())

    def test_unauthorized_image_delete(self):
        """Тест попытки удаления изображения неавторизованным пользователем"""
        self.client.credentials()  # Remove authentication
        
        url = f'/api/images/{self.announcement_image.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(AnnouncementImage.objects.filter(id=self.announcement_image.id).exists()) 