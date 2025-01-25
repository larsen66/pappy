from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from catalog.models import Product, Category
from .models import Dialog, Message
from decimal import Decimal

class ChatTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create(phone='+79991234567')
        self.seller = self.User.objects.create(phone='+79991234568')
        self.other_user = self.User.objects.create(phone='+79991234569')
        self.client.force_login(self.user)
        
        # Создаем тестовую категорию и продукт
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title='Тестовый продукт',
            slug='test-product',
            description='Описание тестового продукта',
            price=Decimal('1000.00'),
            condition='new'
        )
        
        # Создаем диалог
        self.dialog = Dialog.objects.create(product=self.product)
        self.dialog.participants.add(self.user, self.seller)
        
    def test_dialogs_list(self):
        response = self.client.get(reverse('chat:dialogs_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/dialogs_list.html')
        
    def test_dialog_detail(self):
        response = self.client.get(
            reverse('chat:dialog_detail', kwargs={'dialog_id': self.dialog.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/dialog_detail.html')
        
    def test_send_message(self):
        # Отправляем сообщение
        response = self.client.post(
            reverse('chat:send_message', kwargs={'dialog_id': self.dialog.id}),
            {'text': 'Тестовое сообщение'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Message.objects.filter(
                dialog=self.dialog,
                sender=self.user,
                text='Тестовое сообщение'
            ).exists()
        )
        
    def test_create_dialog(self):
        # Удаляем существующий диалог для чистоты теста
        self.dialog.delete()
        
        # Создаем новый диалог
        response = self.client.post(
            reverse('chat:create_dialog', kwargs={'product_id': self.product.id})
        )
        self.assertEqual(response.status_code, 302)  # Редирект после создания
        
        # Проверяем, что диалог создан
        dialog = Dialog.objects.filter(product=self.product).first()
        self.assertIsNotNone(dialog)
        self.assertIn(self.user, dialog.participants.all())
        self.assertIn(self.seller, dialog.participants.all())
    
    def test_dialog_access_permissions(self):
        # Логинимся под другим пользователем
        self.client.force_login(self.other_user)
        
        # Пытаемся получить доступ к диалогу
        response = self.client.get(
            reverse('chat:dialog_detail', kwargs={'dialog_id': self.dialog.id})
        )
        self.assertEqual(response.status_code, 403)  # Доступ запрещен
        
        # Пытаемся отправить сообщение
        response = self.client.post(
            reverse('chat:send_message', kwargs={'dialog_id': self.dialog.id}),
            {'text': 'Тестовое сообщение'}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_message_read_status(self):
        # Отправляем сообщение от продавца
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse('chat:send_message', kwargs={'dialog_id': self.dialog.id}),
            {'text': 'Сообщение от продавца'}
        )
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что сообщение не прочитано
        message = Message.objects.latest('created')
        self.assertFalse(message.is_read)
        
        # Читаем сообщение другим пользователем
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('chat:dialog_detail', kwargs={'dialog_id': self.dialog.id})
        )
        
        # Проверяем, что сообщение помечено как прочитанное
        message.refresh_from_db()
        self.assertTrue(message.is_read)
    
    def test_messages_ordering(self):
        # Создаем несколько сообщений
        messages = [
            Message.objects.create(
                dialog=self.dialog,
                sender=self.user,
                text=f'Сообщение {i}'
            ) for i in range(3)
        ]
        
        # Проверяем порядок сообщений в диалоге
        response = self.client.get(
            reverse('chat:dialog_detail', kwargs={'dialog_id': self.dialog.id})
        )
        
        dialog_messages = response.context['messages']
        self.assertEqual(list(dialog_messages), messages)
    
    def test_dialog_creation_restrictions(self):
        # Пытаемся создать второй диалог для того же продукта
        response = self.client.post(
            reverse('chat:create_dialog', kwargs={'product_id': self.product.id})
        )
        self.assertEqual(response.status_code, 400)  # Ошибка - диалог уже существует
        
        # Пытаемся создать диалог для своего продукта
        product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Мой продукт',
            slug='my-product',
            description='Описание моего продукта',
            price=Decimal('1000.00'),
            condition='new'
        )
        response = self.client.post(
            reverse('chat:create_dialog', kwargs={'product_id': product.id})
        )
        self.assertEqual(response.status_code, 400)  # Ошибка - нельзя создать диалог с самим собой 