from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
import io
from ..models import VerificationDocument, ModerationQueue

User = get_user_model()

class ModerationTests(TestCase):
    def setUp(self):
        # Создаем обычного пользователя
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        
        # Создаем модератора
        self.moderator = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_staff=True
        )
        
        # Создаем тестовый документ
        self.document = self.create_test_document()
        
        # Создаем клиент для тестов
        self.client = Client()
    
    def create_test_document(self):
        """Создание тестового документа"""
        # Создаем тестовое изображение
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        test_image = SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')
        
        # Создаем документ
        document = VerificationDocument.objects.create(
            user=self.user,
            document=test_image,
            document_type='passport',
            comment='Test document'
        )
        return document
    
    def test_moderation_queue_creation(self):
        """Тест создания элемента очереди модерации"""
        queue_item = ModerationQueue.objects.get(document=self.document)
        self.assertEqual(queue_item.priority, 'high')  # Для паспорта приоритет высокий
        self.assertFalse(queue_item.is_processed)
        self.assertIsNotNone(queue_item.deadline)
    
    def test_moderation_queue_view_access(self):
        """Тест доступа к очереди модерации"""
        # Неавторизованный пользователь
        response = self.client.get(reverse('user_profile:moderation_queue'))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа
        self.assertIn('/auth/', response.url)
        
        # Обычный пользователь
        self.client.login(phone='+79991234567', password='testpass123')
        response = self.client.get(reverse('user_profile:moderation_queue'))
        self.assertEqual(response.status_code, 403)  # Доступ запрещен
        
        # Модератор
        self.client.login(phone='+79991234568', password='testpass123')
        response = self.client.get(reverse('user_profile:moderation_queue'))
        self.assertEqual(response.status_code, 200)  # Доступ разрешен
    
    def test_document_processing(self):
        """Тест обработки документа модератором"""
        self.client.login(phone='+79991234568', password='testpass123')
        queue_item = ModerationQueue.objects.get(document=self.document)
        
        # Одобрение документа
        response = self.client.post(reverse('user_profile:process_document', args=[queue_item.id]), {
            'action': 'approve'
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успешной обработки
        
        # Проверяем обновление статуса
        queue_item.refresh_from_db()
        self.document.refresh_from_db()
        self.assertTrue(queue_item.is_processed)
        self.assertEqual(self.document.status, 'approved')
        
        # Проверяем создание уведомления
        self.assertTrue(self.user.notifications.filter(notification_type='system', title='Документ одобрен').exists())
    
    def test_document_rejection(self):
        """Тест отклонения документа"""
        self.client.login(phone='+79991234568', password='testpass123')
        queue_item = ModerationQueue.objects.get(document=self.document)
        
        # Отклонение документа
        response = self.client.post(reverse('user_profile:process_document', args=[queue_item.id]), {
            'action': 'reject',
            'reason': 'Invalid document'
        })
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление статуса
        queue_item.refresh_from_db()
        self.document.refresh_from_db()
        self.assertTrue(queue_item.is_processed)
        self.assertEqual(self.document.status, 'rejected')
        self.assertEqual(self.document.rejection_reason, 'Invalid document')
        
        # Проверяем создание уведомления
        self.assertTrue(self.user.notifications.filter(notification_type='system', title='Документ отклонен').exists())
    
    def test_document_rejection_without_reason(self):
        """Тест отклонения документа без указания причины"""
        self.client.login(phone='+79991234568', password='testpass123')
        queue_item = ModerationQueue.objects.get(document=self.document)
        
        # Попытка отклонения документа без причины
        response = self.client.post(reverse('user_profile:process_document', args=[queue_item.id]), {
            'action': 'reject',
            'reason': ''  # Пустая причина
        })
        self.assertEqual(response.status_code, 200)  # Возвращаемся к форме
        
        # Проверяем, что статус не изменился
        queue_item.refresh_from_db()
        self.document.refresh_from_db()
        self.assertFalse(queue_item.is_processed)
        self.assertEqual(self.document.status, 'pending')
    
    def test_process_nonexistent_document(self):
        """Тест обработки несуществующего документа"""
        self.client.login(phone='+79991234568', password='testpass123')
        
        # Попытка обработки несуществующего документа
        response = self.client.post(reverse('user_profile:process_document', args=[99999]), {
            'action': 'approve'
        })
        self.assertEqual(response.status_code, 404)
    
    def test_process_already_processed_document(self):
        """Тест повторной обработки уже обработанного документа"""
        self.client.login(phone='+79991234568', password='testpass123')
        queue_item = ModerationQueue.objects.get(document=self.document)
        
        # Сначала обрабатываем документ
        response = self.client.post(reverse('user_profile:process_document', args=[queue_item.id]), {
            'action': 'approve'
        })
        self.assertEqual(response.status_code, 302)
        
        # Пытаемся обработать тот же документ еще раз
        response = self.client.post(reverse('user_profile:process_document', args=[queue_item.id]), {
            'action': 'reject',
            'reason': 'Another attempt'
        })
        self.assertEqual(response.status_code, 404)  # Должен вернуть 404, так как документ уже обработан
        
        # Проверяем, что статус не изменился
        queue_item.refresh_from_db()
        self.document.refresh_from_db()
        self.assertTrue(queue_item.is_processed)
        self.assertEqual(self.document.status, 'approved')  # Статус должен остаться approved
    
    def test_invalid_action(self):
        """Тест обработки с неверным действием"""
        self.client.login(phone='+79991234568', password='testpass123')
        queue_item = ModerationQueue.objects.get(document=self.document)
        
        # Попытка выполнить неверное действие
        response = self.client.post(reverse('user_profile:process_document', args=[queue_item.id]), {
            'action': 'invalid_action'
        })
        self.assertEqual(response.status_code, 200)  # Возвращаемся к форме
        
        # Проверяем, что статус не изменился
        queue_item.refresh_from_db()
        self.document.refresh_from_db()
        self.assertFalse(queue_item.is_processed)
        self.assertEqual(self.document.status, 'pending') 