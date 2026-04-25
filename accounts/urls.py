from django.urls import path
from .views import (
    PlatformRegistrationView,
    UserRegistrationView,
    PlatformLoginView,
    UserProfileView,
    PlatformListView,
    UserPlatformsView,
    logout_view,
    platform_info_view,
)

urlpatterns = [
    # Platform management
    path('platforms/', PlatformListView.as_view(), name='platform-list'),
    path('platforms/register/', PlatformRegistrationView.as_view(), name='platform-register'),
    
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', PlatformLoginView.as_view(), name='platform-login'),
    path('logout/', logout_view, name='logout'),
    
    # User management
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('platforms/my/', UserPlatformsView.as_view(), name='user-platforms'),
    path('platform/info/', platform_info_view, name='platform-info'),
]
