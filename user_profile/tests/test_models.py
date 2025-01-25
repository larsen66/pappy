from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
import io

from user_profile.models import SellerProfile, SpecialistProfile

class SellerProfileTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create(
            phone='+79991234567',
            first_name='Иван',
            last_name='Иванов'
        )
        
        # Создаем тестовое изображение
        image = Image.new('RGB', (100, 100), 'red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        self.document = SimpleUploadedFile(
            'test_document.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_seller_profile_creation(self):
        """Тест создания профиля продавца"""
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual',
            description='Тестовое описание',
            document_scan=self.document
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.seller_type, 'individual')
        self.assertEqual(profile.description, 'Тестовое описание')
        self.assertTrue(profile.document_scan)
        self.assertFalse(profile.is_verified)
    
    def test_seller_profile_str(self):
        """Тест строкового представления профиля продавца"""
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        expected_str = f'Профиль продавца {self.user.get_full_name()}'
        self.assertEqual(str(profile), expected_str)
    
    def test_seller_profile_verification(self):
        """Тест верификации профиля продавца"""
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        # Верифицируем профиль
        profile.is_verified = True
        profile.verification_date = timezone.now()
        profile.save()
        
        profile.refresh_from_db()
        self.assertTrue(profile.is_verified)
        self.assertIsNotNone(profile.verification_date)
    
    def test_seller_profile_company_info(self):
        """Тест информации о компании"""
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='company',
            company_name='ООО Тест',
            inn='1234567890',
            website='http://test.com'
        )
        
        self.assertEqual(profile.seller_type, 'company')
        self.assertEqual(profile.company_name, 'ООО Тест')
        self.assertEqual(profile.inn, '1234567890')
        self.assertEqual(profile.website, 'http://test.com')

class SpecialistProfileTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create(
            phone='+79991234567',
            first_name='Иван',
            last_name='Иванов'
        )
        
        # Создаем тестовое изображение
        image = Image.new('RGB', (100, 100), 'red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        self.certificate = SimpleUploadedFile(
            'test_certificate.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_specialist_profile_creation(self):
        """Тест создания профиля специалиста"""
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='veterinarian',
            experience_years=5,
            services='Лечение животных',
            price_range='1000-5000 руб.',
            certificates=self.certificate
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.specialization, 'veterinarian')
        self.assertEqual(profile.experience_years, 5)
        self.assertEqual(profile.services, 'Лечение животных')
        self.assertEqual(profile.price_range, '1000-5000 руб.')
        self.assertTrue(profile.certificates)
    
    def test_specialist_profile_str(self):
        """Тест строкового представления профиля специалиста"""
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='veterinarian'
        )
        expected_str = f'Профиль специалиста {self.user.get_full_name()}'
        self.assertEqual(str(profile), expected_str)
    
    def test_specialist_profile_inheritance(self):
        """Тест наследования от SellerProfile"""
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='veterinarian',
            company_name='Ветклиника',
            inn='1234567890'
        )
        
        # Проверяем поля из SellerProfile
        self.assertEqual(profile.seller_type, 'individual')
        self.assertEqual(profile.company_name, 'Ветклиника')
        self.assertEqual(profile.inn, '1234567890')
        
        # Проверяем поля SpecialistProfile
        self.assertEqual(profile.specialization, 'veterinarian')
    
    def test_specialist_services_and_price(self):
        """Тест услуг и цен специалиста"""
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='groomer',
            services='Стрижка\nМытье\nУкладка',
            price_range='от 2000 руб.'
        )
        
        self.assertEqual(profile.specialization, 'groomer')
        self.assertIn('Стрижка', profile.services)
        self.assertIn('Мытье', profile.services)
        self.assertEqual(profile.price_range, 'от 2000 руб.') 