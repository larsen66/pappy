from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

# Create your tests here.

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.phone = '+79991234567'
        
    def test_registration(self):
        # Тест регистрации
        response = self.client.post(reverse('login_auth:signup'), {
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.User.objects.filter(phone=self.phone).exists())
        
    def test_login(self):
        # Создаем пользователя
        user = self.User.objects.create(phone=self.phone)
        
        # Тест входа
        response = self.client.post(reverse('login_auth:login'), {
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 200)
        
    def test_sms_verification(self):
        # Создаем пользователя и устройство TOTP
        user = self.User.objects.create(phone=self.phone)
        device = TOTPDevice.objects.create(user=user, confirmed=True)
        token = device.generate_token()
        
        # Тест проверки SMS кода
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': token,
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успешной проверки
