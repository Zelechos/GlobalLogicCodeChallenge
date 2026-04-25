from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from .models import Notification, NotificationChannel, NotificationTemplate
from .services import NotificationService
from accounts.models import Platform, UserPlatform

User = get_user_model()


class NotificationServiceTest(TestCase):
    """Test NotificationService functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.platform = Platform.objects.create(name="Test Platform")
        self.user_platform = UserPlatform.objects.create(
            user=self.user,
            platform=self.platform,
            password='testpass123'
        )
        
        # Create default templates
        NotificationService.create_default_templates()
    
    @patch('builtins.print')
    def test_send_notification_with_template(self, mock_print):
        """Test sending notification with template."""
        notification = NotificationService.send_notification(
            notification_type='user_registered',
            user_platform=self.user_platform,
            data={'test': 'data'}
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.notification_type, 'user_registered')
        self.assertEqual(notification.user_platform, self.user_platform)
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_send_notification_custom(self, mock_print):
        """Test sending custom notification."""
        notification = NotificationService.send_notification(
            notification_type='custom_notification',
            recipient=self.user,
            title='Custom Title',
            message='Custom message',
            data={'key': 'value'}
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.notification_type, 'custom_notification')
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, 'Custom Title')
        self.assertEqual(notification.message, 'Custom message')


class NotificationModelTest(TestCase):
    """Test Notification model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type='test_notification',
            title='Test Notification',
            message='Test message',
            data={'key': 'value'}
        )
    
    def test_notification_creation(self):
        """Test notification creation."""
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.notification_type, 'test_notification')
        self.assertEqual(self.notification.title, 'Test Notification')
        self.assertEqual(self.notification.message, 'Test message')
        self.assertFalse(self.notification.is_read)
    
    def test_notification_str(self):
        """Test notification string representation."""
        expected = f"{self.notification.title} - {self.user.email}"
        self.assertEqual(str(self.notification), expected)


class NotificationChannelTest(TestCase):
    """Test NotificationChannel model functionality."""
    
    def test_channel_creation(self):
        """Test notification channel creation."""
        channel = NotificationChannel.objects.create(
            name='Test Channel',
            channel_type='console',
            config={'setting': 'value'}
        )
        
        self.assertEqual(channel.name, 'Test Channel')
        self.assertEqual(channel.channel_type, 'console')
        self.assertTrue(channel.is_active)
        self.assertEqual(channel.config, {'setting': 'value'})


class NotificationAPITest(APITestCase):
    """Test notification API endpoints."""
    
    def setUp(self):
        self.platform = Platform.objects.create(name="Test Platform")
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.user_platform = UserPlatform.objects.create(
            user=self.user,
            platform=self.platform,
            password='testpass123'
        )
        
        # Create some notifications
        self.notification1 = Notification.objects.create(
            recipient=self.user,
            notification_type='test_notification',
            title='Test Notification 1',
            message='Test message 1',
            is_read=False
        )
        self.notification2 = Notification.objects.create(
            recipient=self.user,
            notification_type='test_notification',
            title='Test Notification 2',
            message='Test message 2',
            is_read=True
        )
        
        # Login and get token
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'platform_name': 'Test Platform'
        }
        url = reverse('platform-login')
        response = self.client.post(url, login_data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_list_notifications(self):
        """Test listing notifications."""
        url = reverse('notification-list')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_notifications_by_read_status(self):
        """Test filtering notifications by read status."""
        url = reverse('notification-list')
        response = self.client.get(url + '?is_read=false', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Notification 1')
    
    def test_get_notification_detail(self):
        """Test getting notification details."""
        url = reverse('notification-detail', kwargs={'pk': self.notification1.id})
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Notification 1')
        self.assertEqual(response.data['message'], 'Test message 1')
    
    def test_mark_notification_read(self):
        """Test marking notification as read."""
        url = reverse('mark-notification-read', kwargs={'pk': self.notification1.id})
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
    
    def test_unread_notifications_count(self):
        """Test getting unread notifications count."""
        url = reverse('unread-count')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)
    
    def test_notification_search(self):
        """Test searching notifications."""
        url = reverse('notification-list')
        response = self.client.get(url + '?search=Notification 1', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Notification 1')
    
    def test_notification_ordering(self):
        """Test ordering notifications."""
        url = reverse('notification-list')
        response = self.client.get(url + '?ordering=-created_at', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by creation date descending
        self.assertEqual(response.data['results'][0]['title'], 'Test Notification 2')
        self.assertEqual(response.data['results'][1]['title'], 'Test Notification 1')
