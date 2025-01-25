from typing import Any

from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from loguru import logger

from core_apps.common.permissions import IsAccountExecutive, IsTeller
from core_apps.common.renderers import GenericJSONRenderer

from .models import BankAccount
from .serializers import BankAccountVerificationSerializer, CustomerInfoSerializer, DepositSerializer
from .emails import send_full_activation_email, send_deposite_email

class BankAccountVerificationView(generics.UpdateAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'verification'
    permission_classes = [IsAccountExecutive]

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        if instance.kyc_verified and instance.fully_activated:
            return Response({'message': 'Account is already fully activated.'}, status=status.HTTP_400_BAD_REQUEST)
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
            kyc_submitted = serializer.validated_data.get('kyc_submitted', instance.kyc_submitted)
            kyc_verified = serializer.validated_data.get('kyc_verified', instance.kyc_verified)
            if kyc_verified and not kyc_submitted:
                return Response({'error': 'KYC must be submitted before it can be verified.'}, 
                                status=status.HTTP_400_BAD_REQUEST)
            instance.kyc_submitted = kyc_submitted
            instance.save()

            if kyc_submitted and kyc_verified:
                instance.kyc_verified = kyc_verified
                instance.verification_date = serializer.validated_data.get('verification_date', timezone.now())
                instance.verification_notes = serializer.validated_data.get('verification_notes', '')
                instance.verified_by = request.user
                instance.fully_activated = True
                instance.account_status = BankAccount.AccountStatus.ACTIVE
                instance.save()

                send_full_activation_email(instance)
            return Response({
                'message': 'Account verification status updated successfully',
                'data': self.get_serializer(instance).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepositView(generics.CreateAPIView):
    serializer_class = DepositSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'deposit'
    permission_classes = [IsTeller]
    
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_number = request.query_params.get('account_number')
        if not account_number:
            return Response({'error': 'Account number is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            bank_account = BankAccount.objects.get(account_number=account_number)
            serializer = CustomerInfoSerializer(bank_account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Invalid account number'}, status=status.HTTP_400_BAD_REQUEST)
        
    @transaction.atomic
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bank_account = serializer.context['account']
        amount = serializer.validated_data['amount']
        try:
            bank_account.account_balance += amount
            bank_account.full_clean()
            bank_account.save()
            logger.info(f'Deposit of {amount} made to account {bank_account.account_number} by teller ' + \
                        f'{request.user.email}')
            send_deposite_email(user=bank_account.user, user_email=bank_account.user.email, amount=amount,
                                currency=bank_account.account_currency, new_balance=bank_account.account_balance,
                                account_number=bank_account.account_number)
            return Response({
                'message': f'Deposit amount: {amount} successfully to account {bank_account.account_number}',
                'new_balance': str(bank_account.account_balance),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to deposit {amount} to {bank_account.account_number}, Error: {e}")
            return Response({'error': 'Failed to deposit amount'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
