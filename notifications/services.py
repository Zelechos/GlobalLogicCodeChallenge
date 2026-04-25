from django.utils import timezone
from django.template import Template, Context
from .models import Notification, NotificationChannel, NotificationTemplate
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications."""
    
    @staticmethod
    def send_notification(notification_type, recipient=None, user_platform=None, 
                         title=None, message=None, data=None):
        """
        Send a notification.
        
        Args:
            notification_type: Type of notification
            recipient: User recipient (optional)
            user_platform: UserPlatform recipient (optional)
            title: Custom title (optional, will use template if not provided)
            message: Custom message (optional, will use template if not provided)
            data: Additional data for the notification
        """
        try:
            # Get template for this notification type
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()
            
            if template:
                # Use template if available
                context = Context({
                    'user': recipient,
                    'user_platform': user_platform,
                    'data': data or {},
                    'timestamp': timezone.now()
                })
                
                title = Template(template.title_template).render(context) if not title else title
                message = Template(template.message_template).render(context) if not message else message
                
                # Send through configured channels
                for channel in template.channels.filter(is_active=True):
                    NotificationService._send_through_channel(
                        channel, title, message, recipient, user_platform, data
                    )
            
            # Create notification record
            notification = Notification.objects.create(
                recipient=recipient,
                user_platform=user_platform,
                notification_type=notification_type,
                title=title or f"{notification_type}",
                message=message or f"Notification of type {notification_type}",
                data=data or {}
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            # Fallback to console logging
            print(f"NOTIFICATION: {notification_type} - {title} - {message}")
    
    @staticmethod
    def _send_through_channel(channel, title, message, recipient, user_platform, data):
        """Send notification through a specific channel."""
        if channel.channel_type == 'console':
            print(f"🔔 [{channel.name}] {title}: {message}")
            logger.info(f"Notification [{channel.name}]: {title} - {message}")
        
        elif channel.channel_type == 'email':
            # Email implementation would go here
            print(f"📧 Email to {recipient.email if recipient else 'N/A'}: {title}")
            logger.info(f"Email notification sent: {title}")
        
        elif channel.channel_type == 'webhook':
            # Webhook implementation would go here
            print(f"🔗 Webhook to {channel.config.get('url', 'N/A')}: {title}")
            logger.info(f"Webhook notification sent: {title}")
        
        # Add other channel implementations as needed
    
    @staticmethod
    def create_default_templates():
        """Create default notification templates."""
        templates_data = [
            {
                'notification_type': 'user_registered',
                'title_template': 'Welcome to {{ user_platform.platform.name }}!',
                'message_template': 'Hello {{ user.user.email }}, you have successfully registered on {{ user_platform.platform.name }}.',
            },
            {
                'notification_type': 'device_added',
                'title_template': 'New Device Added',
                'message_template': 'Device "{{ data.device_name }}" has been added to your account on {{ user_platform.platform.name }}.',
            },
            {
                'notification_type': 'login_success',
                'title_template': 'Login Successful',
                'message_template': 'You have successfully logged into {{ user_platform.platform.name }}.',
            },
        ]
        
        # Create console channel if it doesn't exist
        console_channel, created = NotificationChannel.objects.get_or_create(
            name='Console',
            defaults={
                'channel_type': 'console',
                'config': {}
            }
        )
        
        for template_data in templates_data:
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=template_data['notification_type'],
                defaults=template_data
            )
            if created:
                template.channels.add(console_channel)
