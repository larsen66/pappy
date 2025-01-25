from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from user_profile.forms import SellerProfileForm, SpecialistProfileForm

class SellerProfileFormTests(TestCase):
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
    
    def test_seller_profile_form_valid(self):
        """Тест валидной формы продавца"""
        form_data = {
            'seller_type': 'individual',
            'description': 'Тестовое описание'
        }
        form_files = {'document_scan': self.document}
        
        form = SellerProfileForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
    
    def test_seller_profile_form_required_fields(self):
        """Тест обязательных полей формы продавца"""
        form = SellerProfileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('seller_type', form.errors)
    
    def test_seller_profile_form_company_validation(self):
        """Тест валидации полей компании"""
        # Для типа 'company' обязательны дополнительные поля
        form_data = {
            'seller_type': 'company',
            'description': 'Тестовое описание'
        }
        
        form = SellerProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)
        self.assertIn('inn', form.errors)
    
    def test_seller_profile_form_inn_validation(self):
        """Тест валидации ИНН"""
        form_data = {
            'seller_type': 'entrepreneur',
            'inn': '123'  # Неверный формат ИНН
        }
        
        form = SellerProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('inn', form.errors)

class SpecialistProfileFormTests(TestCase):
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
    
    def test_specialist_profile_form_valid(self):
        """Тест валидной формы специалиста"""
        form_data = {
            'seller_type': 'individual',
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Лечение животных',
            'price_range': '1000-5000 руб.'
        }
        form_files = {'certificates': self.certificate}
        
        form = SpecialistProfileForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
    
    def test_specialist_profile_form_required_fields(self):
        """Тест обязательных полей формы специалиста"""
        form = SpecialistProfileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('seller_type', form.errors)
        self.assertIn('specialization', form.errors)
    
    def test_specialist_profile_form_experience_validation(self):
        """Тест валидации опыта работы"""
        form_data = {
            'seller_type': 'individual',
            'specialization': 'veterinarian',
            'experience_years': -1  # Отрицательное значение
        }
        
        form = SpecialistProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('experience_years', form.errors)
    
    def test_specialist_profile_form_services_validation(self):
        """Тест валидации описания услуг"""
        # Слишком длинное описание услуг
        form_data = {
            'seller_type': 'individual',
            'specialization': 'veterinarian',
            'services': 'x' * 1001  # Превышает максимальную длину
        }
        
        form = SpecialistProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('services', form.errors) 