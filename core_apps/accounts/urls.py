from django.urls import path
from .views import BankAccountVerificationView, DepositView, InitiateWithdrawalView, \
    VerifyUsernameAndWithdrawApiView

urlpatterns = [
    path('verify/<uuid:pk>/', BankAccountVerificationView.as_view(), name='account_verification'),
    path('deposit/', DepositView.as_view(), name='account_deposit'),
    path('initiate-withdraw/', InitiateWithdrawalView.as_view(), name='initiate_withdraw'),
    path('verify-username-and-withdraw/', VerifyUsernameAndWithdrawApiView.as_view(), 
         name='verify_username_and_withdraw'),
]
