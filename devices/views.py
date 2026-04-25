from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from .models import Device
from .serializers import DeviceSerializer, DeviceDetailSerializer, DeviceUpdateSerializer
from accounts.models import UserPlatform
from notifications.services import NotificationService


class DeviceListCreateView(generics.ListCreateAPIView):
    """List and create devices for the authenticated user on current platform."""
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'device_type']
    search_fields = ['name', 'ip_address']
    ordering_fields = ['created_at', 'last_seen', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get devices for current user and platform."""
        user_platform_id = getattr(self.request.user, '_user_platform_id', None)
        if not user_platform_id:
            return Device.objects.none()
        
        return Device.objects.filter(
            user_platform_id=user_platform_id
        ).select_related('user_platform__platform', 'user_platform__user')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method == 'POST':
            return DeviceSerializer
        return DeviceDetailSerializer


class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific device."""
    serializer_class = DeviceUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get devices for current user and platform."""
        user_platform_id = getattr(self.request.user, '_user_platform_id', None)
        if not user_platform_id:
            return Device.objects.none()
        
        return Device.objects.filter(
            user_platform_id=user_platform_id
        ).select_related('user_platform__platform', 'user_platform__user')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method in ['PUT', 'PATCH']:
            return DeviceUpdateSerializer
        return DeviceDetailSerializer
    
    def perform_destroy(self, instance):
        """Delete device and send notification."""
        user_platform = instance.user_platform
        
        # Send notification before deletion
        NotificationService.send_notification(
            notification_type='device_removed',
            user_platform=user_platform,
            data={
                'device_name': instance.name,
                'device_id': instance.id,
                'ip_address': instance.ip_address
            }
        )
        
        instance.delete()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_device_last_seen(request, device_id):
    """Update the last_seen timestamp for a device."""
    try:
        user_platform_id = getattr(request.user, '_user_platform_id', None)
        if not user_platform_id:
            return Response(
                {'error': 'Platform information not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device = Device.objects.get(
            id=device_id,
            user_platform_id=user_platform_id
        )
        
        device.update_last_seen()
        
        return Response({
            'message': 'Last seen updated successfully',
            'last_seen': device.last_seen
        })
        
    except Device.DoesNotExist:
        return Response(
            {'error': 'Device not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_statistics_view(request):
    """Get device statistics for the current user on current platform."""
    try:
        user_platform_id = getattr(request.user, '_user_platform_id', None)
        if not user_platform_id:
            return Response(
                {'error': 'Platform information not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_platform = UserPlatform.objects.get(id=user_platform_id)
        platform = user_platform.platform
        
        # Get device statistics
        devices = Device.objects.filter(user_platform_id=user_platform_id)
        
        stats = {
            'total_devices': devices.count(),
            'active_devices': devices.filter(is_active=True).count(),
            'inactive_devices': devices.filter(is_active=False).count(),
            'max_devices_allowed': platform.get_rule('max_devices', 5),
            'devices_remaining': max(0, platform.get_rule('max_devices', 5) - devices.count()),
            'devices_by_type': dict(devices.values_list('device_type', flat=True).annotate(
                count=models.Count('device_type')
            ).values_list('device_type', 'count')),
            'recent_devices': devices.order_by('-last_seen')[:5].values(
                'id', 'name', 'ip_address', 'last_seen', 'is_active'
            )
        }
        
        return Response(stats)
        
    except UserPlatform.DoesNotExist:
        return Response(
            {'error': 'User platform not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
