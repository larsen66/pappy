from django.test import TestCase
from django.contrib.auth import get_user_model
from pets.models import SwipeAction, SwipeHistory, Match, Announcement
from announcements.models import AnnouncementCategory
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SwipeSystemTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(phone='+79001234567', password='pass')
        self.user2 = User.objects.create_user(phone='+79001234568', password='pass')
        
        # Create test category
        self.category = AnnouncementCategory.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test announcements
        self.announcement1 = Announcement.objects.create(
            author=self.user1,
            title='Test Announcement 1',
            description='Test Description 1',
            category=self.category,
            status='active',
            type='animal',
            is_premium=True
        )
        self.announcement2 = Announcement.objects.create(
            author=self.user2,
            title='Test Announcement 2',
            description='Test Description 2',
            category=self.category,
            status='active',
            type='animal',
            is_premium=False
        )

    def test_swipe_creation(self):
        """Test creating a swipe action"""
        swipe = SwipeAction.objects.create(
            user=self.user1,
            announcement=self.announcement2,
            direction=SwipeAction.LIKE
        )
        self.assertEqual(swipe.direction, SwipeAction.LIKE)
        self.assertEqual(swipe.user, self.user1)
        self.assertEqual(swipe.announcement, self.announcement2)

    def test_swipe_uniqueness(self):
        """Test that a user can't swipe the same announcement twice"""
        SwipeAction.objects.create(
            user=self.user1,
            announcement=self.announcement2,
            direction=SwipeAction.LIKE
        )
        with self.assertRaises(Exception):
            SwipeAction.objects.create(
                user=self.user1,
                announcement=self.announcement2,
                direction=SwipeAction.DISLIKE
            )

    def test_mutual_like_creates_match(self):
        """Test that mutual likes create a match"""
        SwipeAction.objects.create(
            user=self.user1,
            announcement=self.announcement2,
            direction=SwipeAction.LIKE
        )
        SwipeAction.objects.create(
            user=self.user2,
            announcement=self.announcement1,
            direction=SwipeAction.LIKE
        )
        match = Match.objects.filter(user1=self.user1, user2=self.user2).first()
        self.assertIsNotNone(match)

    def test_view_history_tracking(self):
        """Test tracking view history"""
        history = SwipeHistory.objects.create(
            user=self.user1,
            announcement=self.announcement2,
            viewed_at=timezone.now()
        )
        self.assertEqual(history.user, self.user1)
        self.assertEqual(history.announcement, self.announcement2)
        self.assertFalse(history.is_returned)

    def test_card_selection_algorithm(self):
        """Test the algorithm for selecting next cards"""
        # Create some viewed announcements
        SwipeHistory.objects.create(
            user=self.user1,
            announcement=self.announcement2,
            viewed_at=timezone.now()
        )
        
        # Create a new premium announcement
        premium_announcement = Announcement.objects.create(
            author=self.user2,
            title='Premium Announcement',
            description='Premium Description',
            category=self.category,
            status='active',
            type='animal',
            is_premium=True
        )
        
        # Get next cards
        from pets.views import SwipeSystem
        next_cards = SwipeSystem.get_next_cards(self.user1)
        
        # Verify we have cards
        self.assertTrue(next_cards.exists())
        
        # Premium announcement should be first
        self.assertEqual(next_cards.first(), premium_announcement)
        # Viewed announcement should not be included
        self.assertNotIn(self.announcement2, next_cards)

    def test_compatibility_check(self):
        """Test compatibility checking for breeding matches"""
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            announcement1=self.announcement1,
            announcement2=self.announcement2,
            is_breeding_match=True
        )
        score = match.check_compatibility()
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1) 