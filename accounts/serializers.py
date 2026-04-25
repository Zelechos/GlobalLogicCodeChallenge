from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Platform, UserPlatform
from notifications.services import NotificationService


class PlatformSerializer(serializers.ModelSerializer):
    """Serializer for Platform model."""
    
    class Meta:
        model = Platform
        fields = ['id', 'name', 'description', 'is_active', 'business_rules', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration on a platform."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    platform_name = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    def validate_platform_name(self, value):
        """Validate that platform exists and is active."""
        try:
            platform = Platform.objects.get(name=value, is_active=True)
            return platform
        except Platform.DoesNotExist:
            raise serializers.ValidationError("Platform not found or inactive.")
    
    def validate_email(self, value):
        """Validate email format."""
        return value.lower()
    
    def create(self, validated_data):
        """Create user and platform membership."""
        platform = validated_data.pop('platform_name')
        email = validated_data['email'].lower()
        password = validated_data.pop('password')
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': validated_data.get('first_name', ''),
                'last_name': validated_data.get('last_name', ''),
            }
        )
        
        if not created:
            # Set password if user exists but might not have one
            user.set_password(password)
            user.save()
        
        # Create UserPlatform membership
        user_platform, platform_created = UserPlatform.objects.get_or_create(
            user=user,
            platform=platform,
            defaults={'password': password}
        )
        
        if not platform_created:
            # Update password if membership exists
            user_platform.password = password
            user_platform.save()
        
        # Send notification
        NotificationService.send_notification(
            notification_type='user_registered',
            user_platform=user_platform,
            data={'platform_name': platform.name}
        )
        
        return user_platform


class LoginSerializer(serializers.Serializer):
    """Serializer for platform-specific login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    platform_name = serializers.CharField(max_length=100)
    
    def validate_platform_name(self, value):
        """Validate that platform exists and is active."""
        try:
            platform = Platform.objects.get(name=value, is_active=True)
            return platform
        except Platform.DoesNotExist:
            raise serializers.ValidationError("Platform not found or inactive.")
    
    def validate(self, attrs):
        """Validate credentials and return user_platform if valid."""
        email = attrs['email'].lower()
        password = attrs['password']
        platform = attrs['platform_name']
        
        try:
            user_platform = UserPlatform.objects.get(
                user__email=email,
                platform=platform,
                is_active=True
            )
            
            # Check if platform allows inactive login
            if not user_platform.user.is_active:
                allow_inactive = platform.get_rule('allow_inactive_login', True)
                if not allow_inactive:
                    raise serializers.ValidationError("User account is inactive.")
            
            # Verify password
            if not user_platform.check_password(password):
                raise serializers.ValidationError("Invalid credentials.")
            
            # Update last login
            from django.utils import timezone
            user_platform.last_login = timezone.now()
            user_platform.save(update_fields=['last_login'])
            
            # Send login notification
            NotificationService.send_notification(
                notification_type='login_success',
                user_platform=user_platform,
                data={'platform_name': platform.name}
            )
            
            attrs['user_platform'] = user_platform
            return attrs
            
        except UserPlatform.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials or user not registered on this platform.")


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""
    platforms = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'platforms']
        read_only_fields = ['id', 'email', 'date_joined']
    
    def get_platforms(self, obj):
        """Get user's platform memberships."""
        memberships = obj.platform_memberships.filter(is_active=True).select_related('platform')
        return [
            {
                'platform_id': membership.platform.id,
                'platform_name': membership.platform.name,
                'joined_at': membership.created_at,
                'last_login': membership.last_login,
                'device_count': membership.devices.count()
            }
            for membership in memberships
        ]
