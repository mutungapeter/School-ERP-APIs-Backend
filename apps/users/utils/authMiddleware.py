from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class AuthTokenMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        protected_urls = [
            
            '/api/v1/teachers/', 
            '/api/v1/students/']

        if request.path in protected_urls:

            authorization_header = request.headers.get('Authorization')
            if authorization_header:
                try:
                    token_type, access_token = authorization_header.split(' ')
                    if token_type == 'Bearer':
                        AccessToken(access_token)
                        # print("Received access token  from frontend:", access_token)
                    else:
                        return JsonResponse({'error': 'Invalid token type'}, status=401)
                except (TokenError, ValueError):

                    # print("Token expired attempting to refresh")
                    refresh_token = request.headers.get('x-refresh-token')
                    if not refresh_token:
                        return JsonResponse({'error': 'Refresh token not found, Please login to continue'}, status=400)

                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access_token = str(refresh.access_token)
                        # print("New accessToken", new_access_token)

                        request.META['HTTP_AUTHORIZATION'] = f'Bearer{new_access_token}'
                        response = self.get_response(request)
                        response.set_cookie(
                            'accessToken', new_access_token, httponly=True, secure=False, samesite='Strict')
                        return response

                    except TokenError as e:
                        return JsonResponse({'error': str(e)}, status=400)

            return self.get_response(request)

        return self.get_response(request)
