from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock
from login_auth.models import OneTimeCode
from login_auth.services import SMSService

User = get_user_model()

@override_settings(
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }]
)
class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = '+79991234567'
        self.test_code = '1234'
    
    @patch('login_auth.services.SMSService.send_sms')
    def test_registration(self, mock_send_sms):
        """Тест регистрации по номеру телефона"""
        response = self.client.post(reverse('login_auth:signup'), {
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login_auth:sms_validation'))
        
        verification = OneTimeCode.objects.filter(phone=self.phone).first()
        self.assertIsNotNone(verification)
        mock_send_sms.assert_called_once()
    
    @patch('login_auth.services.SMSService.send_sms')
    def test_login(self, mock_send_sms):
        """Тест входа в систему"""
        response = self.client.post(reverse('login_auth:phone_login'), {
            'phone': self.phone
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login_auth:sms_validation'))
        
        verification = OneTimeCode.objects.filter(phone=self.phone).first()
        self.assertIsNotNone(verification)
        mock_send_sms.assert_called_once()
    
    def test_phone_login_get(self):
        """Тест GET-запроса страницы входа"""
        response = self.client.get(reverse('login_auth:phone_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login_auth/phone_login.html')
    
    @patch('login_auth.services.SMSService.send_sms')
    def test_sms_verification(self, mock_send_sms):
        """Тест верификации через SMS"""
        # Создаем код подтверждения
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=self.test_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Сохраняем телефон в сессии
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        # Отправляем код
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': self.test_code
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('catalog:home'))
        
        # Проверяем, что пользователь был создан
        user = User.objects.filter(phone=self.phone).first()
        self.assertIsNotNone(user)
        
        # Проверяем, что код был подтвержден
        verification.refresh_from_db()
        self.assertTrue(verification.is_verified)
    
    def test_confirm_code_invalid(self):
        """Тест неверного кода подтверждения"""
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=self.test_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': '654321'  # Неверный код
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login_auth/sms_validation.html')
        
        verification.refresh_from_db()
        self.assertFalse(verification.is_verified)
        self.assertEqual(verification.attempts, 1)
    
    def test_confirm_code_expired(self):
        """Тест истекшего кода подтверждения"""
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=self.test_code,
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': self.test_code
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login_auth:phone_login'))
        
        verification.refresh_from_db()
        self.assertFalse(verification.is_verified)

    def test_phone_login_success(self):
        """Тест успешного входа по номеру телефона"""
        with patch.object(SMSService, 'send_sms', return_value=True):
            response = self.client.post(reverse('login_auth:phone_login'), {'phone': self.phone})
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('login_auth:verify'))
            
            # Проверяем, что код был создан
            verification = OneTimeCode.objects.filter(phone=self.phone).first()
            self.assertIsNotNone(verification)
            self.assertFalse(verification.is_verified)
    
    def test_verify_code_success(self):
        """Тест успешной проверки кода"""
        # Создаем код подтверждения
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=self.test_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        # Сохраняем телефон в сессии
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        # Отправляем код
        response = self.client.post(reverse('login_auth:verify'), {'code': self.test_code})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile:settings'))
        
        # Проверяем, что пользователь создан и авторизован
        self.assertTrue(User.objects.filter(phone=self.phone).exists())
    
    def test_verify_code_invalid(self):
        """Тест неверного кода"""
        # Создаем код подтверждения
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=self.test_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        # Сохраняем телефон в сессии
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        # Отправляем неверный код
        response = self.client.post(reverse('login_auth:verify'), {'code': '9999'})
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что попытка увеличилась
        verification.refresh_from_db()
        self.assertEqual(verification.attempts, 1)
    
    def test_verify_code_expired(self):
        """Тест истекшего кода"""
        # Создаем истекший код
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=self.test_code,
            expires_at=timezone.now() - timezone.timedelta(minutes=1)
        )
        
        # Сохраняем телефон в сессии
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        # Отправляем код
        response = self.client.post(reverse('login_auth:verify'), {'code': self.test_code})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login_auth:phone_login'))
    
    def test_resend_code(self):
        """Тест повторной отправки кода"""
        # Создаем первый код
        old_verification = OneTimeCode.objects.create(
            phone=self.phone,
            code='0000',
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        # Сохраняем телефон в сессии
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        # Запрашиваем новый код
        with patch.object(SMSService, 'send_sms', return_value=True):
            response = self.client.post(reverse('login_auth:resend_code'))
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('login_auth:verify'))
            
            # Проверяем, что старый код удален и создан новый
            self.assertFalse(OneTimeCode.objects.filter(code='0000').exists())
            self.assertTrue(OneTimeCode.objects.filter(phone=self.phone).exists())
    
    def test_gosuslugi_auth(self):
        """Тест авторизации через Госуслуги"""
        response = self.client.post(reverse('login_auth:gosuslugi'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile:settings'))
        
        # Проверяем, что пользователь создан и верифицирован
        user = User.objects.get(phone='+79991234567')
        self.assertTrue(user.is_verified)

class OneTimeCodeTests(TestCase):
    def setUp(self):
        self.phone = '+79991234567'
    
    def test_code_generation(self):
        """Тест генерации кода подтверждения"""
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code=''.join(['0'] * OneTimeCode.CODE_LENGTH),
            expires_at=timezone.now() + timedelta(minutes=OneTimeCode.EXPIRY_TIME_MINUTES)
        )
        
        new_code = verification.generate_code()
        self.assertEqual(len(new_code), OneTimeCode.CODE_LENGTH)
        self.assertTrue(new_code.isdigit())
        self.assertNotEqual(new_code, '0' * OneTimeCode.CODE_LENGTH)
    
    def test_expiry_check(self):
        """Тест проверки срока действия кода"""
        expired_verification = OneTimeCode.objects.create(
            phone=self.phone,
            code='123456',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertTrue(expired_verification.is_expired())
        
        valid_verification = OneTimeCode.objects.create(
            phone=self.phone,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        self.assertFalse(valid_verification.is_expired())
    
    def test_blocking_after_max_attempts(self):
        """Тест блокировки после максимального количества попыток"""
        verification = OneTimeCode.objects.create(
            phone=self.phone,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
            attempts=OneTimeCode.MAX_VERIFICATION_ATTEMPTS
        )
        self.assertTrue(verification.is_blocked())

class SMSServiceTests(TestCase):
    def setUp(self):
        self.phone = '+79991234567'
        self.message = 'Test message'
        self.sms_service = SMSService()

    @patch('login_auth.services.urlopen')
    def test_successful_sms_send(self, mock_urlopen):
        # Мокаем успешный ответ от API
        mock_response = type('Response', (), {
            'read': lambda self: b'100\n12345\n',
            'decode': lambda self, encoding: '100\n12345\n'
        })()
        mock_urlopen.return_value = mock_response

        result = self.sms_service.send_sms(self.phone, self.message)
        self.assertTrue(result)

    @patch('login_auth.services.urlopen')
    def test_failed_sms_send(self, mock_urlopen):
        # Мокаем неуспешный ответ от API
        mock_response = type('Response', (), {
            'read': lambda self: b'201\n',
            'decode': lambda self, encoding: '201\n'
        })()
        mock_urlopen.return_value = mock_response

        result = self.sms_service.send_sms(self.phone, self.message)
        self.assertFalse(result)

    @patch('login_auth.services.urlopen')
    def test_url_error_handling(self, mock_urlopen):
        # Мокаем ошибку соединения
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError('Connection error')

        result = self.sms_service.send_sms(self.phone, self.message)
        self.assertFalse(result) 