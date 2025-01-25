from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
import io

from .models import SellerProfile, SpecialistProfile, VerificationDocument
from .forms import UserProfileForm, SellerProfileForm, SpecialistProfileForm

User = get_user_model()

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_user_profile_creation(self):
        """Тест автоматического создания профиля пользователя"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_update(self):
        """Тест обновления профиля пользователя"""
        response = self.client.post(reverse('user_profile:settings'), {
            'bio': 'Test bio',
            'location': 'Test City'
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Test bio')
        self.assertEqual(self.user.profile.location, 'Test City')

class SellerProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_seller_profile_creation(self):
        """Тест создания профиля продавца"""
        response = self.client.post(reverse('user_profile:create_seller_profile'), {
            'seller_type': 'individual',
            'description': 'Test seller'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(hasattr(self.user, 'seller_profile'))
        self.assertEqual(self.user.seller_profile.seller_type, 'individual')

    def test_seller_verification(self):
        """Тест процесса верификации продавца"""
        seller_profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='company',
            company_name='Test Company',
            inn='1234567890'
        )
        
        # Создаем тестовый файл для загрузки
        test_file = SimpleUploadedFile(
            "test_doc.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('user_profile:verification_request'), {
            'document': test_file,
            'comment': 'Test verification request'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VerificationDocument.objects.filter(user=self.user).exists())

class SpecialistProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_specialist=True
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_specialist_profile_creation(self):
        """Тест создания профиля специалиста"""
        response = self.client.post(reverse('user_profile:create_specialist_profile'), {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services',
            'price_range': '1000-5000'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(hasattr(self.user, 'specialist_profile'))
        self.assertEqual(self.user.specialist_profile.specialization, 'veterinarian')

    def test_specialist_verification(self):
        """Тест процесса верификации специалиста"""
        specialist_profile = SpecialistProfile.objects.create(
            user=self.user,
            specialization='veterinarian',
            experience_years=5,
            services='Test services'
        )
        
        test_file = SimpleUploadedFile(
            "certificate.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('user_profile:verification_request'), {
            'document': test_file,
            'comment': 'Test verification request'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VerificationDocument.objects.filter(user=self.user).exists())

class ProfileFormsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )

    def test_user_profile_form(self):
        """Тест формы профиля пользователя"""
        form_data = {
            'bio': 'Test bio',
            'location': 'Test City'
        }
        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_seller_profile_form(self):
        """Тест формы профиля продавца"""
        form_data = {
            'seller_type': 'individual',
            'description': 'Test seller'
        }
        form = SellerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_specialist_profile_form(self):
        """Тест формы профиля специалиста"""
        form_data = {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services',
            'price_range': '1000-5000'
        }
        form = SpecialistProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_seller_profile_update(self):
        """Тест обновления профиля продавца"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual',
            description='Старое описание'
        )
        
        # Обновляем профиль
        update_data = {
            'seller_type': 'entrepreneur',
            'description': 'Новое описание',
            'inn': '123456789012'
        }
        
        response = self.client.post(
            reverse('user_profile:update_seller_profile'),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление
        profile.refresh_from_db()
        self.assertEqual(profile.seller_type, 'entrepreneur')
        self.assertEqual(profile.description, 'Новое описание')
        self.assertEqual(profile.inn, '123456789012')
    
    def test_specialist_profile_update(self):
        """Тест обновления профиля специалиста"""
        # Создаем профиль
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='groomer',
            experience_years=3
        )
        
        # Обновляем профиль
        update_data = {
            'seller_type': 'entrepreneur',
            'specialization': 'trainer',
            'experience_years': 7,
            'services': 'Дрессировка собак',
            'price_range': '2000-7000 руб.'
        }
        
        response = self.client.post(
            reverse('user_profile:update_specialist_profile'),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление
        profile.refresh_from_db()
        self.assertEqual(profile.specialization, 'trainer')
        self.assertEqual(profile.experience_years, 7)
        self.assertEqual(profile.services, 'Дрессировка собак')
    
    def test_profile_verification(self):
        """Тест верификации профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        # Отправляем на верификацию
        response = self.client.post(
            reverse('user_profile:request_verification'),
            {'document_scan': self.document}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем статус верификации
        profile.refresh_from_db()
        self.assertFalse(profile.is_verified)  # Пока не подтверждено модератором
        
        # Подтверждаем верификацию (как модератор)
        admin_user = self.User.objects.create(
            phone='+79991234568',
            is_staff=True
        )
        self.client.force_login(admin_user)
        
        response = self.client.post(
            reverse('user_profile:verify_profile', kwargs={'user_id': self.user.id}),
            {'is_verified': True}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем результат верификации
        profile.refresh_from_db()
        self.assertTrue(profile.is_verified)
        self.assertIsNotNone(profile.verification_date)
    
    def test_profile_access_permissions(self):
        """Тест прав доступа к профилю"""
        # Создаем другого пользователя
        other_user = self.User.objects.create(phone='+79991234569')
        other_profile = SellerProfile.objects.create(
            user=other_user,
            seller_type='individual'
        )
        
        # Пытаемся обновить чужой профиль
        update_data = {'description': 'Попытка взлома'}
        response = self.client.post(
            reverse('user_profile:update_seller_profile', kwargs={'user_id': other_user.id}),
            update_data
        )
        self.assertEqual(response.status_code, 403)  # Доступ запрещен
        
        # Проверяем, что данные не изменились
        other_profile.refresh_from_db()
        self.assertNotEqual(other_profile.description, 'Попытка взлома')
    
    def test_profile_deletion(self):
        """Тест удаления профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        # Удаляем профиль
        response = self.client.post(reverse('user_profile:delete_profile'))
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что профиль удален
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_profile_type_validation(self):
        """Тест валидации типа профиля"""
        # Пытаемся создать профиль с неверным типом
        profile_data = {
            'seller_type': 'invalid_type',
            'description': 'Тестовое описание'
        }
        
        response = self.client.post(
            reverse('user_profile:create_seller_profile'),
            profile_data
        )
        self.assertEqual(response.status_code, 200)  # Форма с ошибками
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_inn_validation(self):
        """Тест валидации ИНН"""
        # Пытаемся создать профиль с неверным ИНН
        profile_data = {
            'seller_type': 'entrepreneur',
            'inn': '123'  # Слишком короткий ИНН
        }
        
        response = self.client.post(
            reverse('user_profile:create_seller_profile'),
            profile_data
        )
        self.assertEqual(response.status_code, 200)  # Форма с ошибками
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_specialist_experience_validation(self):
        """Тест валидации опыта работы специалиста"""
        # Пытаемся создать профиль с отрицательным опытом
        profile_data = {
            'seller_type': 'individual',
            'specialization': 'veterinarian',
            'experience_years': -1
        }
        
        response = self.client.post(
            reverse('user_profile:create_specialist_profile'),
            profile_data
        )
        self.assertEqual(response.status_code, 200)  # Форма с ошибками
        self.assertFalse(SpecialistProfile.objects.filter(user=self.user).exists()) 