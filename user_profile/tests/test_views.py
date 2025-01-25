from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from user_profile.models import SellerProfile, SpecialistProfile

class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create(
            phone='+79991234567',
            first_name='Иван',
            last_name='Иванов'
        )
        self.other_user = self.User.objects.create(
            phone='+79991234568',
            first_name='Петр',
            last_name='Петров'
        )
        self.client.force_login(self.user)
        
        # Создаем тестовое изображение
        image = Image.new('RGB', (100, 100), 'red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        self.document = SimpleUploadedFile(
            'test_document.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_profile_create_view(self):
        """Тест создания профиля"""
        response = self.client.get(reverse('user_profile:create_seller_profile'))
        self.assertEqual(response.status_code, 200)
        
        # Отправляем POST-запрос для создания профиля
        profile_data = {
            'seller_type': 'individual',
            'description': 'Тестовое описание'
        }
        files = {'document_scan': self.document}
        
        response = self.client.post(
            reverse('user_profile:create_seller_profile'),
            data=profile_data,
            files=files
        )
        self.assertEqual(response.status_code, 302)  # Редирект после создания
        
        # Проверяем, что профиль создан
        self.assertTrue(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_profile_update_view(self):
        """Тест обновления профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        response = self.client.get(reverse('user_profile:update_seller_profile'))
        self.assertEqual(response.status_code, 200)
        
        # Обновляем профиль
        update_data = {
            'seller_type': 'entrepreneur',
            'description': 'Новое описание',
            'inn': '123456789012'
        }
        
        response = self.client.post(
            reverse('user_profile:update_seller_profile'),
            data=update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление
        profile.refresh_from_db()
        self.assertEqual(profile.seller_type, 'entrepreneur')
        self.assertEqual(profile.description, 'Новое описание')
    
    def test_specialist_profile_create_view(self):
        """Тест создания профиля специалиста"""
        response = self.client.get(reverse('user_profile:create_specialist_profile'))
        self.assertEqual(response.status_code, 200)
        
        # Отправляем POST-запрос для создания профиля
        profile_data = {
            'seller_type': 'individual',
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Лечение животных',
            'price_range': '1000-5000 руб.'
        }
        files = {'certificates': self.document}
        
        response = self.client.post(
            reverse('user_profile:create_specialist_profile'),
            data=profile_data,
            files=files
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что профиль создан
        self.assertTrue(SpecialistProfile.objects.filter(user=self.user).exists())
    
    def test_profile_access_permissions(self):
        """Тест прав доступа к профилю"""
        # Создаем профиль для другого пользователя
        other_profile = SellerProfile.objects.create(
            user=self.other_user,
            seller_type='individual'
        )
        
        # Пытаемся получить доступ к чужому профилю
        response = self.client.get(
            reverse('user_profile:update_seller_profile', kwargs={'user_id': self.other_user.id})
        )
        self.assertEqual(response.status_code, 403)  # Доступ запрещен
        
        # Пытаемся обновить чужой профиль
        update_data = {'description': 'Попытка взлома'}
        response = self.client.post(
            reverse('user_profile:update_seller_profile', kwargs={'user_id': self.other_user.id}),
            data=update_data
        )
        self.assertEqual(response.status_code, 403)
    
    def test_profile_verification_view(self):
        """Тест верификации профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        # Отправляем запрос на верификацию
        response = self.client.post(
            reverse('user_profile:request_verification'),
            {'document_scan': self.document}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем статус верификации
        profile.refresh_from_db()
        self.assertFalse(profile.is_verified)  # Пока не подтверждено модератором
    
    def test_profile_delete_view(self):
        """Тест удаления профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        response = self.client.post(reverse('user_profile:delete_profile'))
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что профиль удален
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_profile_list_view(self):
        """Тест списка специалистов"""
        # Создаем несколько профилей специалистов
        SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='veterinarian'
        )
        SpecialistProfile.objects.create(
            user=self.other_user,
            seller_type='individual',
            specialization='groomer'
        )
        
        response = self.client.get(reverse('user_profile:specialist_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['specialists']), 2)
    
    def test_profile_detail_view(self):
        """Тест детальной страницы профиля"""
        # Создаем профиль специалиста
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='veterinarian',
            services='Лечение животных',
            price_range='1000-5000 руб.'
        )
        
        response = self.client.get(
            reverse('user_profile:specialist_detail', kwargs={'pk': profile.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['specialist'], profile)
    
    def test_profile_search_view(self):
        """Тест поиска специалистов"""
        # Создаем профили с разными специализациями
        SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='veterinarian',
            services='Лечение животных'
        )
        SpecialistProfile.objects.create(
            user=self.other_user,
            seller_type='individual',
            specialization='groomer',
            services='Стрижка собак'
        )
        
        # Поиск по специализации
        response = self.client.get(
            reverse('user_profile:specialist_list'),
            {'specialization': 'veterinarian'}
        )
        self.assertEqual(len(response.context['specialists']), 1)
        
        # Поиск по услугам
        response = self.client.get(
            reverse('user_profile:specialist_list'),
            {'q': 'Стрижка'}
        )
        self.assertEqual(len(response.context['specialists']), 1) 