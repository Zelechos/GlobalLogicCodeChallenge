from django.db import models
from django.core.validators import RegexValidator
from accounts.models import UserPlatform


class Device(models.Model):
    """Represents a device associated with a user on a specific platform."""
    user_platform = models.ForeignKey(
        UserPlatform, 
        on_delete=models.CASCADE, 
        related_name='devices'
    )
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional device information
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(
        max_length=50,
        choices=[
            ('mobile', 'Mobile'),
            ('desktop', 'Desktop'),
            ('tablet', 'Tablet'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    class Meta:
        db_table = 'devices_device'
        unique_together = ['user_platform', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.user_platform.user.email})"
    
    def update_last_seen(self):
        """Update the last_seen timestamp."""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    @classmethod
    def validate_ip_address(cls, ip_address, platform_rules):
        """Validate IP address based on platform rules."""
        if not platform_rules.get('ip_validation_enabled', False):
            return True
        
        # Add IP validation logic here based on platform rules
        # For now, just basic format validation
        try:
            from ipaddress import ip_address
            ip_address(ip_address)
            return True
        except ValueError:
            return False
