from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Device
from accounts.models import Platform, UserPlatform

User = get_user_model()


class DeviceModelTest(TestCase):
    """Test Device model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.platform = Platform.objects.create(
            name="Test Platform",
            business_rules={'max_devices': 5}
        )
        self.user_platform = UserPlatform.objects.create(
            user=self.user,
            platform=self.platform,
            password='testpass123'
        )
        self.device = Device.objects.create(
            user_platform=self.user_platform,
            name="Test Device",
            ip_address="192.168.1.100"
        )
    
    def test_device_creation(self):
        """Test device creation."""
        self.assertEqual(self.device.name, "Test Device")
        self.assertEqual(self.device.ip_address, "192.168.1.100")
        self.assertTrue(self.device.is_active)
        self.assertEqual(self.device.user_platform, self.user_platform)
    
    def test_update_last_seen(self):
        """Test updating last_seen timestamp."""
        original_last_seen = self.device.last_seen
        self.device.update_last_seen()
        self.assertNotEqual(self.device.last_seen, original_last_seen)
    
    def test_validate_ip_address(self):
        """Test IP address validation."""
        # Valid IP
        self.assertTrue(Device.validate_ip_address("192.168.1.1", {}))
        
        # Invalid IP
        self.assertFalse(Device.validate_ip_address("invalid.ip", {}))


class DeviceAPITest(APITestCase):
    """Test device API endpoints."""
    
    def setUp(self):
        self.platform = Platform.objects.create(
            name="Test Platform",
            business_rules={'max_devices': 3}
        )
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
        
        self.device_data = {
            'name': 'New Device',
            'ip_address': '192.168.1.200',
            'device_type': 'mobile'
        }
    
    def test_create_device(self):
        """Test device creation endpoint."""
        url = reverse('device-list-create')
        response = self.client.post(url, self.device_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Device.objects.filter(name='New Device').exists())
        self.assertEqual(Device.objects.count(), 1)
    
    def test_list_devices(self):
        """Test device listing endpoint."""
        # Create a device first
        Device.objects.create(
            user_platform=self.user_platform,
            name="Test Device",
            ip_address="192.168.1.100"
        )
        
        url = reverse('device-list-create')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Device')
    
    def test_device_limit_enforcement(self):
        """Test device limit enforcement."""
        # Create devices up to the limit
        for i in range(3):
            Device.objects.create(
                user_platform=self.user_platform,
                name=f"Device {i}",
                ip_address=f"192.168.1.{i+1}"
            )
        
        # Try to create one more device
        url = reverse('device-list-create')
        response = self.client.post(url, self.device_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Maximum device limit', str(response.data))
    
    def test_get_device_detail(self):
        """Test getting device details."""
        device = Device.objects.create(
            user_platform=self.user_platform,
            name="Test Device",
            ip_address="192.168.1.100"
        )
        
        url = reverse('device-detail', kwargs={'pk': device.id})
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Device')
        self.assertIn('platform_name', response.data)
        self.assertIn('user_email', response.data)
    
    def test_update_device(self):
        """Test updating device."""
        device = Device.objects.create(
            user_platform=self.user_platform,
            name="Test Device",
            ip_address="192.168.1.100"
        )
        
        update_data = {
            'name': 'Updated Device',
            'ip_address': '192.168.1.101'
        }
        
        url = reverse('device-detail', kwargs={'pk': device.id})
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        device.refresh_from_db()
        self.assertEqual(device.name, 'Updated Device')
        self.assertEqual(device.ip_address, '192.168.1.101')
    
    def test_delete_device(self):
        """Test deleting device."""
        device = Device.objects.create(
            user_platform=self.user_platform,
            name="Test Device",
            ip_address="192.168.1.100"
        )
        
        url = reverse('device-detail', kwargs={'pk': device.id})
        response = self.client.delete(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Device.objects.filter(id=device.id).exists())
    
    def test_update_last_seen(self):
        """Test updating device last_seen timestamp."""
        device = Device.objects.create(
            user_platform=self.user_platform,
            name="Test Device",
            ip_address="192.168.1.100"
        )
        
        original_last_seen = device.last_seen
        
        url = reverse('update-last-seen', kwargs={'device_id': device.id})
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        device.refresh_from_db()
        self.assertNotEqual(device.last_seen, original_last_seen)
    
    def test_device_statistics(self):
        """Test device statistics endpoint."""
        # Create some devices
        for i in range(2):
            Device.objects.create(
                user_platform=self.user_platform,
                name=f"Device {i}",
                ip_address=f"192.168.1.{i+1}",
                is_active=i == 0
            )
        
        url = reverse('device-statistics')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_devices'], 2)
        self.assertEqual(response.data['active_devices'], 1)
        self.assertEqual(response.data['inactive_devices'], 1)
        self.assertEqual(response.data['max_devices_allowed'], 3)
        self.assertEqual(response.data['devices_remaining'], 1)
    
    def test_device_filtering(self):
        """Test device filtering functionality."""
        # Create devices with different properties
        Device.objects.create(
            user_platform=self.user_platform,
            name="Active Device",
            ip_address="192.168.1.100",
            is_active=True,
            device_type='mobile'
        )
        Device.objects.create(
            user_platform=self.user_platform,
            name="Inactive Device",
            ip_address="192.168.1.101",
            is_active=False,
            device_type='desktop'
        )
        
        # Test filtering by is_active
        url = reverse('device-list-create')
        response = self.client.get(url + '?is_active=true', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active Device')
        
        # Test filtering by device_type
        response = self.client.get(url + '?device_type=mobile', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active Device')
    
    def test_device_search(self):
        """Test device search functionality."""
        Device.objects.create(
            user_platform=self.user_platform,
            name="iPhone Device",
            ip_address="192.168.1.100"
        )
        Device.objects.create(
            user_platform=self.user_platform,
            name="Android Device",
            ip_address="192.168.1.101"
        )
        
        url = reverse('device-list-create')
        response = self.client.get(url + '?search=iPhone', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'iPhone Device')
