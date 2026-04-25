from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, 
    LoginSerializer, 
    UserProfileSerializer,
    PlatformSerializer
)
from .models import Platform, UserPlatform
from notifications.services import NotificationService


User = get_user_model()


class PlatformRegistrationView(generics.CreateAPIView):
    """Register a new platform."""
    serializer_class = PlatformSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        platform = serializer.save()
        # Set default business rules
        platform.business_rules = Platform.get_default_rules()
        platform.save()
        
        # Send notification
        NotificationService.send_notification(
            notification_type='platform_created',
            title=f"New Platform Created: {platform.name}",
            message=f"Platform '{platform.name}' has been created successfully.",
            data={'platform_id': platform.id, 'platform_name': platform.name}
        )


class UserRegistrationView(generics.CreateAPIView):
    """Register a user on a specific platform."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class PlatformLoginView(TokenObtainPairView):
    """Custom login view for platform-specific authentication."""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_platform = serializer.validated_data['user_platform']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user_platform.user)
        
        # Add platform information to token payload
        refresh['platform_id'] = user_platform.platform.id
        refresh['platform_name'] = user_platform.platform.name
        refresh['user_platform_id'] = user_platform.id
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user_platform.user.id,
                'email': user_platform.user.email,
                'first_name': user_platform.user.first_name,
                'last_name': user_platform.user.last_name,
            },
            'platform': {
                'id': user_platform.platform.id,
                'name': user_platform.platform.name,
                'business_rules': user_platform.platform.business_rules,
            },
            'user_platform_id': user_platform.id,
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PlatformListView(generics.ListAPIView):
    """List all active platforms."""
    serializer_class = PlatformSerializer
    permission_classes = [AllowAny]
    queryset = Platform.objects.filter(is_active=True)


class UserPlatformsView(generics.ListAPIView):
    """List platforms where the current user is registered."""
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_platforms = UserPlatform.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('platform')
        return [up.platform for up in user_platforms]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout user by blacklisting refresh token."""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def platform_info_view(request):
    """Get current platform information from JWT token."""
    try:
        # Extract platform info from JWT token
        platform_id = getattr(request.user, '_platform_id', None)
        platform_name = getattr(request.user, '_platform_name', None)
        user_platform_id = getattr(request.user, '_user_platform_id', None)
        
        if not platform_id:
            return Response(
                {'error': 'Platform information not found in token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
            user_platform = UserPlatform.objects.get(
                id=user_platform_id,
                user=request.user,
                platform=platform,
                is_active=True
            )
            
            return Response({
                'platform': {
                    'id': platform.id,
                    'name': platform.name,
                    'description': platform.description,
                    'business_rules': platform.business_rules,
                },
                'user_platform_id': user_platform.id,
                'device_count': user_platform.devices.count(),
                'max_devices': platform.get_rule('max_devices', 5),
            })
            
        except (Platform.DoesNotExist, UserPlatform.DoesNotExist):
            return Response(
                {'error': 'Platform or user platform not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
