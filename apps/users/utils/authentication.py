from apps.users.models import User
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken, TokenError

class CustomAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return None

        try:
            token_type, access_token = authorization_header.split(' ')
            if token_type != 'Bearer':
                raise AuthenticationFailed('Invalid token type')
            token = AccessToken(access_token)
        except (TokenError, ValueError):
            raise AuthenticationFailed('Invalid access token')
        
      
        decoded_token = AccessToken(access_token)
        user_id = decoded_token.get('user_id')
        print("userid->", user_id)
        if not user_id:
                raise AuthenticationFailed('Token does not contain user_id')

        user = User.objects.get(id=user_id)
        
        return (user, token)
