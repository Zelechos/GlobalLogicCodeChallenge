from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings


class PlatformJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that extracts platform information."""
    
    def get_validated_token(self, raw_token):
        """Validate token and extract platform information."""
        validated_token = super().get_validated_token(raw_token)
        
        # Extract platform information from token payload
        platform_id = validated_token.get('platform_id')
        platform_name = validated_token.get('platform_name')
        user_platform_id = validated_token.get('user_platform_id')
        
        if not all([platform_id, platform_name, user_platform_id]):
            raise InvalidToken('Token missing required platform information')
        
        return validated_token
    
    def get_user(self, validated_token):
        """Get user and attach platform information."""
        user = super().get_user(validated_token)
        
        # Attach platform information to user object
        user._platform_id = validated_token.get('platform_id')
        user._platform_name = validated_token.get('platform_name')
        user._user_platform_id = validated_token.get('user_platform_id')
        
        return user
