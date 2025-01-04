from django.urls import path

from .views import CustomTokenCreateView, CustomRefreshToken, OTPVerifyView, LogoutApiView

urlpatterns = [
    path('login/', CustomTokenCreateView.as_view(), name='login'),
    path('verify-otp/', OTPVerifyView.as_view(), name='verify_otp'),
    path('refresh/', CustomRefreshToken.as_view(), name='refresh'),
    path('logout/', LogoutApiView.as_view(), name='logout'),
]
