from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Platform, UserPlatform

User = get_user_model()


class PlatformModelTest(TestCase):
    """Test Platform model functionality."""
    
    def setUp(self):
        self.platform = Platform.objects.create(
            name="Test Platform",
            description="Test platform description"
        )
    
    def test_platform_creation(self):
        """Test platform creation."""
        self.assertEqual(self.platform.name, "Test Platform")
        self.assertEqual(self.platform.description, "Test platform description")
        self.assertTrue(self.platform.is_active)
    
    def test_get_default_rules(self):
        """Test default business rules."""
        default_rules = Platform.get_default_rules()
        self.assertIn('max_devices', default_rules)
        self.assertIn('allow_inactive_login', default_rules)
        self.assertEqual(default_rules['max_devices'], 5)
    
    def test_get_rule(self):
        """Test getting specific business rule."""
        self.platform.set_rule('max_devices', 10)
        self.assertEqual(self.platform.get_rule('max_devices'), 10)
        self.assertEqual(self.platform.get_rule('nonexistent', 'default'), 'default')


class UserPlatformModelTest(TestCase):
    """Test UserPlatform model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.platform = Platform.objects.create(
            name="Test Platform",
            business_rules={'max_devices': 3}
        )
        self.user_platform = UserPlatform.objects.create(
            user=self.user,
            platform=self.platform,
            password='testpass123'
        )
    
    def test_user_platform_creation(self):
        """Test user platform membership creation."""
        self.assertEqual(self.user_platform.user, self.user)
        self.assertEqual(self.user_platform.platform, self.platform)
        self.assertTrue(self.user_platform.is_active)
    
    def test_can_add_device(self):
        """Test device limit checking."""
        # Initially should be able to add devices
        self.assertTrue(self.user_platform.can_add_device())
        
        # Add devices up to limit
        from devices.models import Device
        for i in range(3):
            Device.objects.create(
                user_platform=self.user_platform,
                name=f"Device {i}",
                ip_address=f"192.168.1.{i+1}"
            )
        
        # Should not be able to add more devices
        self.assertFalse(self.user_platform.can_add_device())


class AuthenticationAPITest(APITestCase):
    """Test authentication API endpoints."""
    
    def setUp(self):
        self.platform = Platform.objects.create(
            name="Test Platform",
            business_rules={'max_devices': 5}
        )
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'platform_name': 'Test Platform',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        url = reverse('user-register')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        self.assertTrue(UserPlatform.objects.filter(
            user__email='test@example.com',
            platform=self.platform
        ).exists())
    
    def test_user_login(self):
        """Test user login endpoint."""
        # Register user first
        url = reverse('user-register')
        self.client.post(url, self.user_data, format='json')
        
        # Login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'platform_name': 'Test Platform'
        }
        url = reverse('platform-login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('platform', response.data)
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass',
            'platform_name': 'Test Platform'
        }
        url = reverse('platform-login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_platform_registration(self):
        """Test platform registration endpoint."""
        platform_data = {
            'name': 'New Platform',
            'description': 'A new test platform'
        }
        url = reverse('platform-register')
        response = self.client.post(url, platform_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Platform.objects.filter(name='New Platform').exists())


class UserProfileAPITest(APITestCase):
    """Test user profile API endpoints."""
    
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
    
    def test_get_user_profile(self):
        """Test getting user profile."""
        url = reverse('user-profile')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_get_user_platforms(self):
        """Test getting user's platforms."""
        url = reverse('user-platforms')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Platform')
    
    def test_platform_info(self):
        """Test getting current platform info."""
        url = reverse('platform-info')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('platform', response.data)
        self.assertIn('user_platform_id', response.data)
        self.assertIn('device_count', response.data)
