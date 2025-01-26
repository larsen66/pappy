from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from user_profile.models import UserProfile, SellerProfile, SpecialistProfile
from user_profile.forms import UserProfileForm, SellerProfileForm, SpecialistProfileForm
import os

User = get_user_model()

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = '+79991234567'
        self.user = User.objects.create_user(phone=self.phone)
        self.client.force_login(self.user)
        
        # Создаем профиль для пользователя
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.bio = 'Test bio'
        self.profile.location = 'Test location'
        self.profile.save()
    
    def test_profile_update(self):
        """Тест обновления профиля"""
        data = {
            'bio': 'Updated bio',
            'location': 'Updated location'
        }
        
        response = self.client.post(reverse('user_profile:settings'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile:settings'))
        
        # Проверяем, что данные обновились
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio')
        self.assertEqual(self.profile.location, 'Updated location')
    
    def test_profile_settings_get(self):
        """Тест GET-запроса страницы настроек профиля"""
        response = self.client.get(reverse('user_profile:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/settings.html')
        
        # Проверяем, что форма содержит текущие данные профиля
        self.assertContains(response, self.profile.bio)
        self.assertContains(response, self.profile.location)

class SellerProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = '+79991234567'
        self.user = User.objects.create_user(phone=self.phone)
        self.client.force_login(self.user)
        
        # Создаем профиль продавца
        self.seller_profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual',
            inn='123456789012'
        )
    
    def test_seller_profile_update(self):
        """Тест обновления профиля продавца"""
        data = {
            'seller_type': 'company',
            'company_name': 'Test Company',
            'inn': '123456789012',
            'description': 'Test description',
            'website': 'http://example.com'
        }
        
        response = self.client.post(reverse('user_profile:seller_profile'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile:seller_profile'))
        
        # Проверяем, что данные обновились
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller_profile.seller_type, 'company')
        self.assertEqual(self.seller_profile.company_name, 'Test Company')
        self.assertEqual(self.seller_profile.inn, '123456789012')
    
    def test_inn_validation(self):
        """Тест валидации ИНН"""
        # Тест с неверным ИНН
        data = {
            'seller_type': 'individual',
            'inn': '123'  # Неверный формат ИНН
        }
        
        form = SellerProfileForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('inn', form.errors)
        
        # Тест с верным ИНН
        data['inn'] = '123456789012'
        form = SellerProfileForm(data)
        self.assertTrue(form.is_valid())

class SpecialistProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = '+79991234567'
        self.user = User.objects.create_user(phone=self.phone)
        self.client.force_login(self.user)
        
        # Создаем профиль специалиста
        self.specialist_profile = SpecialistProfile.objects.create(
            user=self.user,
            specialization='veterinarian',
            experience_years=5,
            services='Test services',
            price_range='1000-5000'
        )
    
    def test_specialist_profile_update(self):
        """Тест обновления профиля специалиста"""
        data = {
            'specialization': 'groomer',
            'experience_years': 7,
            'services': 'Updated services',
            'price_range': '2000-7000'
        }
        
        response = self.client.post(reverse('user_profile:specialist_profile'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile:specialist_profile'))
        
        # Проверяем, что данные обновились
        self.specialist_profile.refresh_from_db()
        self.assertEqual(self.specialist_profile.specialization, 'groomer')
        self.assertEqual(self.specialist_profile.experience_years, 7)
        self.assertEqual(self.specialist_profile.services, 'Updated services')
    
    def test_experience_validation(self):
        """Тест валидации опыта работы"""
        # Тест с отрицательным опытом
        data = {
            'specialization': 'veterinarian',
            'experience_years': -1,
            'services': 'Test services',
            'price_range': '1000-5000'
        }
        
        form = SpecialistProfileForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('experience_years', form.errors)
        
        # Тест с корректным опытом
        data['experience_years'] = 5
        form = SpecialistProfileForm(data)
        self.assertTrue(form.is_valid())

class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = '+79991234567'
        self.user = User.objects.create_user(phone=self.phone)
        self.client.force_login(self.user)
        
        # Создаем профиль для пользователя
        self.profile = Profile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            inn='123456789012'
        )
    
    def test_profile_update(self):
        """Тест обновления профиля"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'inn': '123456789012',
            'is_seller': True
        }
        
        response = self.client.post(reverse('profiles:settings'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profiles:settings'))
        
        # Проверяем, что данные обновились
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.first_name, 'Updated')
        self.assertEqual(self.profile.last_name, 'Name')
        self.assertTrue(self.profile.is_seller)
    
    def test_inn_validation(self):
        """Тест валидации ИНН"""
        # Тест с неверным ИНН
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'inn': '123'  # Неверный формат ИНН
        }
        
        form = ProfileForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('inn', form.errors)
        
        # Тест с верным ИНН
        data['inn'] = '123456789012'
        form = ProfileForm(data)
        self.assertTrue(form.is_valid())
    
    def test_profile_image_upload(self):
        """Тест загрузки изображения профиля"""
        # Создаем тестовое изображение
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile('test_image.gif', image_content, content_type='image/gif')
        
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'inn': '123456789012',
            'avatar': image
        }
        
        response = self.client.post(reverse('profiles:settings'), data, format='multipart')
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что изображение сохранилось
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.avatar)
        
        # Очищаем файл после теста
        if self.profile.avatar:
            if os.path.exists(self.profile.avatar.path):
                os.remove(self.profile.avatar.path)
    
    def test_profile_image_delete(self):
        """Тест удаления изображения профиля"""
        # Сначала загружаем изображение
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile('test_image.gif', image_content, content_type='image/gif')
        
        self.profile.avatar = image
        self.profile.save()
        
        # Запоминаем путь к файлу
        image_path = self.profile.avatar.path
        
        # Отправляем запрос на удаление
        response = self.client.post(reverse('profiles:delete_avatar'))
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что изображение удалено
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.avatar)
        self.assertFalse(os.path.exists(image_path))
    
    def test_profile_settings_get(self):
        """Тест GET-запроса страницы настроек профиля"""
        response = self.client.get(reverse('profiles:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/settings.html')
        
        # Проверяем, что форма содержит текущие данные профиля
        self.assertContains(response, self.profile.first_name)
        self.assertContains(response, self.profile.last_name)
        self.assertContains(response, self.profile.inn) 