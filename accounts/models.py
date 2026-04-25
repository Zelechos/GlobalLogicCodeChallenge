from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
import json


class Platform(models.Model):
    """Represents a platform with configurable business rules."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configurable business rules stored as JSON
    business_rules = models.JSONField(default=dict, help_text="Platform-specific business rules")
    
    def __str__(self):
        return self.name
    
    def get_rule(self, rule_name, default=None):
        """Get a specific business rule value."""
        return self.business_rules.get(rule_name, default)
    
    def set_rule(self, rule_name, value):
        """Set a specific business rule value."""
        self.business_rules[rule_name] = value
        self.save()
    
    @classmethod
    def get_default_rules(cls):
        """Get default business rules for new platforms."""
        return {
            'max_devices': 5,
            'allow_inactive_login': True,
            'device_name_required': True,
            'ip_validation_enabled': False,
            'session_timeout_hours': 24
        }


class User(AbstractUser):
    """Custom user model using email as primary identifier."""
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'auth_user'
    
    def __str__(self):
        return self.email


class UserPlatform(models.Model):
    """Represents a user's registration on a specific platform."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='platform_memberships')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='user_memberships')
    password = models.CharField(max_length=128)  # Platform-specific password
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'platform']
        db_table = 'accounts_user_platform'
    
    def __str__(self):
        return f"{self.user.email} - {self.platform.name}"
    
    def can_add_device(self):
        """Check if user can add more devices based on platform rules."""
        from devices.models import Device
        max_devices = self.platform.get_rule('max_devices', 5)
        current_devices = Device.objects.filter(
            user_platform=self
        ).count()
        return current_devices < max_devices
