import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from announcements.models import LostFoundAnnouncement, Announcement
from announcements.services import LostPetMatchingService, LostPetSuggestionService
from math import radians, sin, cos, sqrt, atan2

User = get_user_model()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

class TestLostPetAnnouncement(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a base announcement
        self.announcement = Announcement.objects.create(
            user=self.user,
            title='Lost Dog',
            description='My dog is lost',
            status='active'
        )
        
        # Create a lost pet announcement
        self.lost_pet = LostFoundAnnouncement.objects.create(
            announcement=self.announcement,
            type='lost',
            animal_type='dog',
            breed='Labrador',
            color='black',
            date_lost_found=timezone.now(),
            location='Test Location',
            latitude=40.7128,
            longitude=-74.0060,
            distinctive_features='White spot on chest'
        )

    def test_lost_pet_creation(self):
        """Test that lost pet announcement is created correctly"""
        self.assertEqual(self.lost_pet.type, 'lost')
        self.assertEqual(self.lost_pet.animal_type, 'dog')
        self.assertEqual(self.lost_pet.breed, 'Labrador')
        self.assertTrue(self.lost_pet.latitude)
        self.assertTrue(self.lost_pet.longitude)

    def test_geolocation(self):
        """Test geolocation functionality"""
        self.assertEqual(float(self.lost_pet.latitude), 40.7128)
        self.assertEqual(float(self.lost_pet.longitude), -74.0060)

class TestLostPetMatching(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a lost pet announcement
        self.lost_announcement = Announcement.objects.create(
            user=self.user,
            title='Lost Dog',
            status='active'
        )
        
        self.lost_pet = LostFoundAnnouncement.objects.create(
            announcement=self.lost_announcement,
            type='lost',
            animal_type='dog',
            breed='Labrador',
            color='black',
            date_lost_found=timezone.now(),
            location='Location 1',
            latitude=40.7128,
            longitude=-74.0060,
            distinctive_features='White spot'
        )
        
        # Create a found pet announcement (potential match)
        self.found_announcement = Announcement.objects.create(
            user=self.user,
            title='Found Dog',
            status='active'
        )
        
        self.found_pet = LostFoundAnnouncement.objects.create(
            announcement=self.found_announcement,
            type='found',
            animal_type='dog',
            breed='Labrador',
            color='black',
            date_lost_found=timezone.now(),
            location='Location 2',
            latitude=40.7130,
            longitude=-74.0062,
            distinctive_features='White spot on chest'
        )
        
        self.matching_service = LostPetMatchingService()

    def test_find_matches(self):
        """Test that matching service finds potential matches"""
        matches = self.matching_service.find_matches(self.lost_pet)
        self.assertTrue(len(matches) > 0)
        
        # Check that the found pet is in matches
        found_match = next((m for m in matches if m['match'].id == self.found_pet.id), None)
        self.assertIsNotNone(found_match)
        self.assertTrue(found_match['score'] > 0.3)

    def test_distance_calculation(self):
        """Test distance calculation between lost and found pets"""
        distance = calculate_distance(
            self.lost_pet.latitude, 
            self.lost_pet.longitude,
            self.found_pet.latitude, 
            self.found_pet.longitude
        )
        # The test coordinates are very close (about 0.3 km apart)
        self.assertLess(distance, 0.5)

    def test_no_matches_different_type(self):
        """Test that no matches are found for same type announcements"""
        # Create another lost pet announcement
        another_lost = LostFoundAnnouncement.objects.create(
            announcement=Announcement.objects.create(
                user=self.user,
                title='Another Lost Dog',
                status='active'
            ),
            type='lost',
            animal_type='dog',
            breed='Labrador',
            color='black',
            date_lost_found=timezone.now(),
            location='Location 3',
            latitude=40.7129,
            longitude=-74.0061,
            distinctive_features='White spot'
        )
        
        matches = self.matching_service.find_matches(self.lost_pet)
        another_lost_match = next((m for m in matches if m['match'].id == another_lost.id), None)
        self.assertIsNone(another_lost_match)

class TestLostPetSuggestions(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.announcement = Announcement.objects.create(
            user=self.user,
            title='Lost Dog',
            status='active'
        )
        
        self.lost_pet = LostFoundAnnouncement.objects.create(
            announcement=self.announcement,
            type='lost',
            animal_type='dog',
            breed='Labrador',
            color='black',
            date_lost_found=timezone.now(),
            location='Test Location',
            latitude=40.7128,
            longitude=-74.0060,
            distinctive_features='White spot'
        )
        
        self.suggestion_service = LostPetSuggestionService()

    def test_get_suggestions(self):
        """Test that suggestion service returns suggestions"""
        suggestions = self.suggestion_service.get_suggestions(self.lost_pet)
        self.assertTrue(len(suggestions) > 0)
        
        # Check for popular places category
        popular_places = next((s for s in suggestions if s['category'] == 'popular_places'), None)
        self.assertIsNotNone(popular_places)
        self.assertTrue(len(popular_places['items']) > 0)

    def test_similar_cases(self):
        """Test that similar cases are found"""
        # Create a successful similar case
        successful_announcement = Announcement.objects.create(
            user=self.user,
            title='Found Similar Dog',
            status='closed'
        )
        
        successful_case = LostFoundAnnouncement.objects.create(
            announcement=successful_announcement,
            type='lost',
            animal_type='dog',
            breed='Labrador',
            color='black',
            date_lost_found=timezone.now() - timedelta(days=30),
            location='Similar Location',
            latitude=40.7129,
            longitude=-74.0061,
            distinctive_features='White spot',
            search_history={
                'searched_areas': ['Park', 'Streets'],
                'success_factors': ['Found in park']
            }
        )
        
        suggestions = self.suggestion_service.get_suggestions(self.lost_pet)
        similar_cases = next((s for s in suggestions if s['category'] == 'similar_cases'), None)
        
        self.assertIsNotNone(similar_cases)
        self.assertTrue(len(similar_cases['items']) > 0)
        
        # Check that our successful case is included
        case = next((c for c in similar_cases['items'] if c['type'] == 'similar_case'), None)
        self.assertIsNotNone(case)
        self.assertTrue('search_areas' in case)
        self.assertTrue('success_factors' in case) 