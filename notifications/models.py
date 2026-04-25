from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserPlatform
import json


class Notification(models.Model):
    """Represents a notification in the system."""
    NOTIFICATION_TYPES = [
        ('user_registered', 'User Registered'),
        ('device_added', 'Device Added'),
        ('device_removed', 'Device Removed'),
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('platform_created', 'Platform Created'),
    ]
    
    recipient = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True
    )
    user_platform = models.ForeignKey(
        UserPlatform,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, help_text="Additional data for the notification")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient}"


class NotificationChannel(models.Model):
    """Represents a channel for sending notifications."""
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('webhook', 'Webhook'),
        ('console', 'Console/Log'),
    ]
    
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, help_text="Channel-specific configuration")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications_channel'
    
    def __str__(self):
        return f"{self.name} ({self.channel_type})"


class NotificationTemplate(models.Model):
    """Template for different types of notifications."""
    notification_type = models.CharField(max_length=50, unique=True)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    channels = models.ManyToManyField(NotificationChannel, related_name='templates')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications_template'
    
    def __str__(self):
        return f"{self.notification_type} Template"
