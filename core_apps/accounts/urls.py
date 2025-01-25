from django.urls import path
from .views import BankAccountVerificationView, DepositView

urlpatterns = [
    path('verify/<uuid:pk>/', BankAccountVerificationView.as_view(), name='account_verification'),
    path('deposit/', DepositView.as_view(), name='account_deposit'),
]
