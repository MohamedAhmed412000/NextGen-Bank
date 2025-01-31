from typing import Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from djoser.views import TokenCreateView
from loguru import logger
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .emails import send_otp_email
from core_apps.common.utils import generate_otp
from .serializers import OTPVerifySerializer

User = get_user_model()

def set_auth_cookies(response: Response, access_token: str, refresh_token: Optional[str] = None) -> None:
    access_token_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
    access_cookie_settings = {
        'path': settings.COOKIE_PATH,
        'secure': settings.COOKIE_SECURE,
        'httponly': settings.COOKIE_HTTPONLY,
        'samesite': settings.COOKIE_SAMESITE,
        'max_age': access_token_lifetime,
    }
    response.set_cookie('access', access_token, **access_cookie_settings)

    if refresh_token:
        refresh_cookie_settings = access_cookie_settings.copy()
        refresh_cookie_settings['max_age'] = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
        response.set_cookie('refresh', refresh_token, **refresh_cookie_settings)

    logged_in_cookie_settings = access_cookie_settings.copy()
    logged_in_cookie_settings['httponly'] = False
    response.set_cookie('logged_in', 'true', **logged_in_cookie_settings)
    
class CustomTokenCreateView(TokenCreateView):
    def _action(self, serializer):
        user = serializer.user
        if user.is_locked:
            return Response({
                'error': 'Account is locked due to multiple failed login attempts. '
                f'Please try again after {settings.LOCKOUT_DURATION.total_seconds() // 60} minutes.'
            }, status=status.HTTP_403_FORBIDDEN)
        user.reset_failed_login_attempts()

        otp = generate_otp()
        user.set_otp(otp)
        send_otp_email(user.email, otp)

        logger.info(f'OTP sent for login to user: {user.email}')
        return Response({
            'success': 'OTP sent to your email',
            'email': user.email
        }, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: {
                'description': 'User login successful',
                'type': 'object',
                'properties': {
                    'success': {'type': 'string', 'example': 'OTP sent to your email'},
                    'email': {'type': 'string', 'example': 'user@example.com'},
                },
            },
            400: {
                'description': 'User login failed',
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string', 
                        'example': 'Invalid credentials'
                    },
                },
            },
            403: {
                'description': 'User login failed',
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string', 
                        'example': 'You have exceeded the maximum number of login attempts. Your account is locked for 30 minutes. An email has been sent to you with further instructions'
                    },
                },
            },
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            email = request.data.get('email')
            user = User.objects.filter(email=email).first()
            if user:
                user.handle_failed_login_attempts()
                failed_attempts = user.failed_login_attempts
                logger.error(f'Failed login attempt for user: {user.email}, failed attempts: {failed_attempts}')
                if failed_attempts >= settings.LOGIN_ATTEMPTS:
                    return Response({
                        'error': 'You have exceeded the maximum number of login attempts. '
                        f'Your account is locked for {settings.LOCKOUT_DURATION.total_seconds() // 60} minutes. '
                        'An email has been sent to you with further instructions'
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                logger.error(f'Failed login attempt for non-existing user: {email}')
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return self._action(serializer)

class CustomRefreshToken(TokenRefreshView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data['access']
            refresh_token = response.data['refresh']
    
            if access_token and refresh_token:
                set_auth_cookies(response, access_token, refresh_token)

                response.data.pop('access', None)
                response.data.pop('refresh', None)

                response.data['message'] = 'Access Token refreshed successfully'
        else:
            response.data['message'] = 'Access or refresh token not found in request cookies'
            logger.error('Access or refresh token not found in request cookies')

        return response
    
class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=OTPVerifySerializer,
        responses={
            200: {
                'description': 'OTP verification successful',
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'string',
                        'example': 'Login successful. Now add your profile information, so that we can create an account for you.',
                    }
                },
            }, 
            400: {
                'description': 'Bad request response',
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'OTP is required',
                    }
                },
            },
            403: {
                'description': 'Forbidden response',
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Account is locked due to multiple failed login attempts. Please try again after 30 minutes.',
                    }
                },
            },
        })
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        otp = request.data.get('otp')
        if not otp:
            return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(otp=otp, otp_expiry_time__gt=timezone.now()).first()
        if not user:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_locked:
            return Response({
                'error': 'Account is locked due to multiple failed login attempts. '
                f'Please try again after {settings.LOCKOUT_DURATION.total_seconds() // 60} minutes.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user.verify_otp(otp)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        respone = Response({
            'success': 'Login successful. Now add your profile information, '
            'so that we can create an account for you.',
        }, status=status.HTTP_200_OK)

        set_auth_cookies(respone, access_token, refresh_token)
        logger.info(f'User logged in successfully with OTP: {user.email}')
        return respone
    
class LogoutApiView(APIView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access', path=settings.COOKIE_PATH)
        response.delete_cookie('refresh', path=settings.COOKIE_PATH)
        response.delete_cookie('logged_in', path=settings.COOKIE_PATH)
        return response
