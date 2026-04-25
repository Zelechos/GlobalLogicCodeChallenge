from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Device
from accounts.models import UserPlatform
from notifications.services import NotificationService


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model."""
    
    class Meta:
        model = Device
        fields = [
            'id', 'name', 'ip_address', 'is_active', 'last_seen', 
            'created_at', 'user_agent', 'device_type'
        ]
        read_only_fields = ['id', 'last_seen', 'created_at']
    
    def validate_ip_address(self, value):
        """Validate IP address format."""
        try:
            from ipaddress import ip_address
            ip_address(value)
            return value
        except ValueError:
            raise serializers.ValidationError("Invalid IP address format.")
    
    def validate_name(self, value):
        """Validate device name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Device name is required.")
        return value.strip()
    
    def create(self, validated_data):
        """Create device with platform validation."""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context required.")
        
        # Get user_platform from JWT token
        user_platform_id = getattr(request.user, '_user_platform_id', None)
        if not user_platform_id:
            raise serializers.ValidationError("Platform information not found.")
        
        try:
            user_platform = UserPlatform.objects.get(
                id=user_platform_id,
                user=request.user,
                is_active=True
            )
        except UserPlatform.DoesNotExist:
            raise serializers.ValidationError("User platform not found.")
        
        # Check platform business rules
        platform = user_platform.platform
        
        # Check if device name is required
        if platform.get_rule('device_name_required', True) and not validated_data.get('name'):
            raise serializers.ValidationError("Device name is required for this platform.")
        
        # Check if user can add more devices
        if not user_platform.can_add_device():
            max_devices = platform.get_rule('max_devices', 5)
            raise serializers.ValidationError(
                f"Maximum device limit ({max_devices}) reached for this platform."
            )
        
        # Validate IP address if platform requires it
        if platform.get_rule('ip_validation_enabled', False):
            if not Device.validate_ip_address(validated_data['ip_address'], platform.business_rules):
                raise serializers.ValidationError("IP address validation failed.")
        
        # Create device
        device = Device.objects.create(
            user_platform=user_platform,
            **validated_data
        )
        
        # Send notification
        NotificationService.send_notification(
            notification_type='device_added',
            user_platform=user_platform,
            data={
                'device_name': device.name,
                'device_id': device.id,
                'ip_address': device.ip_address
            }
        )
        
        return device


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Device model."""
    platform_name = serializers.CharField(source='user_platform.platform.name', read_only=True)
    user_email = serializers.CharField(source='user_platform.user.email', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'name', 'ip_address', 'is_active', 'last_seen', 
            'created_at', 'user_agent', 'device_type', 'platform_name', 'user_email'
        ]
        read_only_fields = ['id', 'last_seen', 'created_at', 'platform_name', 'user_email']


class DeviceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating device information."""
    
    class Meta:
        model = Device
        fields = ['name', 'ip_address', 'is_active', 'user_agent', 'device_type']
    
    def validate_ip_address(self, value):
        """Validate IP address format."""
        try:
            from ipaddress import ip_address
            ip_address(value)
            return value
        except ValueError:
            raise serializers.ValidationError("Invalid IP address format.")
