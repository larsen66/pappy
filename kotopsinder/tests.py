from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import Product, Category
from login_auth.models import SellerVerification
from chat.models import Dialog
from .models import Swipe, SwipeHistory
from decimal import Decimal

class KotopsinderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create(phone='+79991234567')
        self.seller = self.User.objects.create(phone='+79991234568')
        
        # Создаем верификацию продавца
        self.seller_verification = SellerVerification.objects.create(
            user=self.seller,
            status='approved',
            passport_scan=SimpleUploadedFile("passport.pdf", b"file_content"),
            selfie_with_passport=SimpleUploadedFile("selfie.jpg", b"file_content")
        )
        
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
        
    def test_swipe_view(self):
        response = self.client.get(reverse('kotopsinder:swipe'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'kotopsinder/swipe.html')
        
    def test_record_swipe(self):
        # Тестируем лайк
        response = self.client.post(
            reverse('kotopsinder:record_swipe'),
            {'product_id': self.product.id, 'direction': 'like'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Swipe.objects.filter(
                user=self.user,
                product=self.product,
                direction='like'
            ).exists()
        )
        
        # Проверяем создание диалога после лайка
        self.assertTrue(
            Dialog.objects.filter(
                participants=self.user
            ).filter(
                participants=self.seller
            ).exists()
        )
        
        # Тестируем дизлайк
        response = self.client.post(
            reverse('kotopsinder:record_swipe'),
            {'product_id': self.product.id, 'direction': 'dislike'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Swipe.objects.filter(
                user=self.user,
                product=self.product,
                direction='dislike'
            ).exists()
        )
        
    def test_swipe_history(self):
        # Проверяем запись истории просмотров
        SwipeHistory.objects.create(user=self.user, product=self.product)
        self.assertTrue(
            SwipeHistory.objects.filter(
                user=self.user,
                product=self.product
            ).exists()
        )
        
    def test_undo_swipe(self):
        # Создаем свайп
        swipe = Swipe.objects.create(
            user=self.user,
            product=self.product,
            direction='like'
        )
        
        # Отменяем свайп
        response = self.client.post(reverse('kotopsinder:undo_swipe'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Swipe.objects.filter(id=swipe.id).exists()
        )
        
    def test_get_next_cards(self):
        response = self.client.get(reverse('kotopsinder:next_cards'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('cards', data)
        
        if data['cards']:
            card = data['cards'][0]
            self.assertEqual(card['title'], self.product.title)
            self.assertEqual(card['seller_verified'], True)  # Продавец верифицирован, так как status='approved'
            self.assertEqual(card['category_name'], self.category.name) 