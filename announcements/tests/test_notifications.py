from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from announcements.models import Announcement, LostFoundAnnouncement
from chat.consumers import NotificationConsumer
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

class TestLostPetNotifications(TestCase):
    async def setUp(self):
        self.user = await sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test announcement
        self.announcement = await sync_to_async(Announcement.objects.create)(
            user=self.user,
            title='Lost Dog',
            status='active'
        )
        
        self.lost_pet = await sync_to_async(LostFoundAnnouncement.objects.create)(
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
        
        # Create nearby user (about 0.3 km away)
        self.nearby_user = await sync_to_async(User.objects.create_user)(
            username='nearbyuser',
            email='nearby@example.com',
            password='testpass123',
            last_latitude=40.7130,
            last_longitude=-74.0062
        )
        
        # Create far away user (about 5 km away)
        self.far_user = await sync_to_async(User.objects.create_user)(
            username='faruser',
            email='far@example.com',
            password='testpass123',
            last_latitude=40.7484,
            last_longitude=-73.9862
        )
        
        self.channel_layer = get_channel_layer()

    async def test_websocket_connection(self):
        """Test that users can connect to the notification websocket"""
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/"
        )
        communicator.scope["user"] = self.user
        connected, _ = await communicator.connect()
        
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_nearby_user_notification(self):
        """Test that nearby users receive notifications"""
        # Calculate distance to verify user is nearby
        distance = calculate_distance(
            self.lost_pet.latitude,
            self.lost_pet.longitude,
            self.nearby_user.last_latitude,
            self.nearby_user.last_longitude
        )
        self.assertLess(distance, 1.0)  # Should be less than 1 km away
        
        # Connect nearby user to websocket
        nearby_communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/"
        )
        nearby_communicator.scope["user"] = self.nearby_user
        await nearby_communicator.connect()
        
        # Simulate sending notification
        await self.channel_layer.group_send(
            f'notifications_{self.nearby_user.id}',
            {
                'type': 'notification.message',
                'message': {
                    'type': 'lost_pet',
                    'announcement_id': self.announcement.id,
                    'title': 'Lost Pet in Your Area',
                    'body': f'A {self.lost_pet.breed} was lost near you'
                }
            }
        )
        
        # Check if notification was received
        response = await nearby_communicator.receive_json_from()
        self.assertEqual(response['type'], 'lost_pet')
        self.assertEqual(response['announcement_id'], self.announcement.id)
        
        await nearby_communicator.disconnect()

    async def test_far_user_no_notification(self):
        """Test that users far away don't receive notifications"""
        # Calculate distance to verify user is far
        distance = calculate_distance(
            self.lost_pet.latitude,
            self.lost_pet.longitude,
            self.far_user.last_latitude,
            self.far_user.last_longitude
        )
        self.assertGreater(distance, 5.0)  # Should be more than 5 km away
        
        # Connect far user to websocket
        far_communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/"
        )
        far_communicator.scope["user"] = self.far_user
        await far_communicator.connect()
        
        # Try to send notification to far user's group
        await self.channel_layer.group_send(
            f'notifications_{self.far_user.id}',
            {
                'type': 'notification.message',
                'message': {
                    'type': 'lost_pet',
                    'announcement_id': self.announcement.id,
                    'title': 'Lost Pet in Your Area',
                    'body': f'A {self.lost_pet.breed} was lost'
                }
            }
        )
        
        # Verify that notification was not received (timeout)
        try:
            await far_communicator.receive_json_from()
            self.fail("Far user should not receive notification")
        except TimeoutError:
            pass  # Expected behavior
        
        await far_communicator.disconnect()

    async def test_notification_radius(self):
        """Test that notifications respect the configured radius"""
        # Create users at different distances
        users_at_distances = [
            (1, True),   # 1km away - should receive
            (3, True),   # 3km away - should receive
            (5, True),   # 5km away - should receive
            (6, False),  # 6km away - should not receive
            (10, False), # 10km away - should not receive
        ]
        
        base_lat = float(self.lost_pet.latitude)
        base_lon = float(self.lost_pet.longitude)
        
        for km, should_receive in users_at_distances:
            # Create user at specified distance (approximate using 111.32 km per degree)
            user = await sync_to_async(User.objects.create_user)(
                username=f'user_{km}km',
                email=f'user_{km}@example.com',
                password='testpass123',
                last_latitude=base_lat + (km / 111.32),
                last_longitude=base_lon
            )
            
            # Verify distance calculation
            distance = calculate_distance(base_lat, base_lon, user.last_latitude, user.last_longitude)
            self.assertAlmostEqual(distance, km, delta=0.1)
            
            # Connect user to websocket
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(),
                "/ws/notifications/"
            )
            communicator.scope["user"] = user
            await communicator.connect()
            
            # Send notification
            await self.channel_layer.group_send(
                f'notifications_{user.id}',
                {
                    'type': 'notification.message',
                    'message': {
                        'type': 'lost_pet',
                        'announcement_id': self.announcement.id,
                        'title': 'Lost Pet in Your Area',
                        'body': f'A {self.lost_pet.breed} was lost'
                    }
                }
            )
            
            if should_receive:
                response = await communicator.receive_json_from()
                self.assertEqual(response['type'], 'lost_pet')
            else:
                try:
                    await communicator.receive_json_from()
                    self.fail(f"User at {km}km should not receive notification")
                except TimeoutError:
                    pass  # Expected behavior
            
            await communicator.disconnect() 