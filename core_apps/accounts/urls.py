from django.urls import path
from .views import BankAccountVerificationView, DepositView, InitiateWithdrawalView, \
        VerifyUsernameAndWithdrawApiView, InitiateTransferView, VerifySecurityQuestionAndTransferApiView, \
        VerifyOTPAndTransferView, TransactionListApiView, TransactionPDFApiView

urlpatterns = [
    path('verify/<uuid:pk>/', BankAccountVerificationView.as_view(), name='account_verification'),
    path('deposit/', DepositView.as_view(), name='account_deposit'),
    path('initiate-withdraw/', InitiateWithdrawalView.as_view(), name='initiate_withdraw'),
    path('verify-username-and-withdraw/', VerifyUsernameAndWithdrawApiView.as_view(), 
         name='verify_username_and_withdraw'),
    path('transfer/initiate/', InitiateTransferView.as_view(), name='initiate_transfer'),
    path('transfer/verify-security-question/', VerifySecurityQuestionAndTransferApiView.as_view(), 
         name='verify_security_question'),
    path('transfer/verify-otp/', VerifyOTPAndTransferView.as_view(), name='verify_otp'),
    path('transactions/', TransactionListApiView.as_view(), name='transaction_list'),
    path('transactions/pdf/', TransactionPDFApiView.as_view(), name='transaction_pdf'),
]
