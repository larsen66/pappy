from django.test import TransactionTestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from login_auth.models import User
from catalog.models import Category, Product
from kotopsinder.models import Swipe, SwipeHistory
from chat.models import Dialog

class KotopsinderTest(TransactionTestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            phone='+79997654321',
            password='seller123',
            is_seller=True
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Create category
        self.category = Category.objects.create(
            name='Кошки',
            description='Кошки всех пород'
        )
        
        # Create test image
        self.image = SimpleUploadedFile(
            "cat.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        # Create product
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title='Британский котенок',
            description='Милый котенок',
            price=15000,
            condition='new',
            status='active',
            breed='Британская',
            age=3,
            size='small'
        )
    
    def test_swipe_right_creates_dialog(self):
        """
        Test that when user swipes right (likes):
        1. Swipe is recorded
        2. Chat dialog is created
        """
        response = self.client.post(reverse('kotopsinder:swipe'), {
            'product': self.product.id,
            'direction': 'right'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check swipe was recorded
        self.assertTrue(
            Swipe.objects.filter(
                user=self.user,
                product=self.product,
                direction='right'
            ).exists()
        )
        
        # Check dialog was created
        self.assertTrue(
            Dialog.objects.filter(
                participants__in=[self.user, self.seller]
            ).exists()
        )
    
    def test_swipe_left_no_dialog(self):
        """Test that left swipe doesn't create dialog"""
        response = self.client.post(reverse('kotopsinder:swipe'), {
            'product': self.product.id,
            'direction': 'left'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check swipe was recorded
        self.assertTrue(
            Swipe.objects.filter(
                user=self.user,
                product=self.product,
                direction='left'
            ).exists()
        )
        
        # Check no dialog was created
        self.assertFalse(
            Dialog.objects.filter(
                participants__in=[self.user, self.seller]
            ).exists()
        )
    
    def test_swipe_history(self):
        """Test that swipe history is recorded"""
        # View product first
        self.client.get(reverse('catalog:product_detail', 
                              kwargs={'slug': self.product.slug}))
        
        # Check history was recorded
        self.assertTrue(
            SwipeHistory.objects.filter(
                user=self.user,
                product=self.product
            ).exists()
        )
    
    def test_no_self_products(self):
        """Test that users don't see their own products in kotopsinder"""
        # Create product owned by user
        own_product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Мой котенок',
            description='Описание',
            price=10000,
            condition='new',
            status='active'
        )
        
        response = self.client.get(reverse('kotopsinder:next_cards'))
        self.assertEqual(response.status_code, 200)
        
        # Own product should not be in response
        self.assertNotIn(own_product.id, 
                        [p['id'] for p in response.json()['products']])
    
    def test_no_swiped_products(self):
        """Test that already swiped products don't appear again"""
        # Swipe on product
        self.client.post(reverse('kotopsinder:swipe'), {
            'product': self.product.id,
            'direction': 'left'
        })
        
        response = self.client.get(reverse('kotopsinder:next_cards'))
        self.assertEqual(response.status_code, 200)
        
        # Swiped product should not be in response
        self.assertNotIn(self.product.id, 
                        [p['id'] for p in response.json()['products']])
    
    def test_undo_last_swipe(self):
        """Test that last swipe can be undone"""
        # Make a swipe
        self.client.post(reverse('kotopsinder:swipe'), {
            'product': self.product.id,
            'direction': 'left'
        })
        
        # Undo it
        response = self.client.post(reverse('kotopsinder:undo_swipe'))
        self.assertEqual(response.status_code, 200)
        
        # Check swipe was removed
        self.assertFalse(
            Swipe.objects.filter(
                user=self.user,
                product=self.product
            ).exists()
        )
        
        # Product should appear in next cards again
        response = self.client.get(reverse('kotopsinder:next_cards'))
        self.assertIn(self.product.id, 
                     [p['id'] for p in response.json()['products']]) 