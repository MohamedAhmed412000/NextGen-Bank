from django.urls import path
from .views import BankAccountVerificationView

urlpatterns = [
    path('verify/<uuid:pk>/', BankAccountVerificationView.as_view(), name='account_verification'),
]
