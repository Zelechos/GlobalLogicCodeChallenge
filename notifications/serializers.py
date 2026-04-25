from rest_framework import serializers
from .models import Notification, NotificationChannel, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    platform_name = serializers.CharField(source='user_platform.platform.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'data',
            'is_read', 'created_at', 'platform_name'
        ]
        read_only_fields = ['id', 'created_at', 'platform_name']


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Serializer for NotificationChannel model."""
    
    class Meta:
        model = NotificationChannel
        fields = ['id', 'name', 'channel_type', 'is_active', 'config', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model."""
    channels = NotificationChannelSerializer(many=True, read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'notification_type', 'title_template', 'message_template',
            'channels', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
