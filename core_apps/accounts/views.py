from typing import Any

from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from loguru import logger

from core_apps.common.permissions import IsAccountExecutive, IsTeller
from core_apps.common.renderers import GenericJSONRenderer
from core_apps.common.utils import generate_otp

from .models import BankAccount, Transaction
from .serializers import BankAccountVerificationSerializer, CustomerInfoSerializer, DepositSerializer, \
    TransactionSerializer, UsernameVerificationSerializer, SecurityQuestionSerializer, OTPVerificationSerializer
from .emails import send_full_activation_email, send_deposite_email, send_withdrawal_email, send_transfer_email, \
    send_transfer_otp_email

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

class InitiateWithdrawalView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'initiate_withdrawal'

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_number = request.data.get('account_number')
        amount = request.data.get('amount')
        if not account_number:
            return Response({'error': 'Account number is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            bank_account = BankAccount.objects.get(account_number=account_number, user=request.user) 
            if not (bank_account.fully_activated and bank_account.kyc_verified):
                return Response({'error': 'Account isn\'t fully verified'}, status=status.HTTP_403_FORBIDDEN)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Invalid account number'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data = {
            'amount': amount,
            'description': f'Withdrawal initiated from account {account_number}',
            'transaction_type': Transaction.TransactionType.WITHDRAW,
            'sender_account': account_number,
            'receiver_account': account_number
        })
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        amount = serializer.validated_data['amount']
        if bank_account.account_balance < amount:
            return Response({'error': 'Insufficient funds for withdraw'}, status=status.HTTP_400_BAD_REQUEST)
        request.session['withdrawal_data'] = {
            'account_number': account_number,
            'amount': str(amount)
        }
        logger.info('Withdraw data is saved in session')
        return Response({
            'message': 'Withdrawal initiated successfully, Please verify your username to complete the withdrawal',
            'next_step': 'Verify your username to complete the withdrawal'
        }, status=status.HTTP_200_OK)

class VerifyUsernameAndWithdrawApiView(generics.CreateAPIView):
    serializer_class = UsernameVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label ='verify_username_and_withdraw'

    @transaction.atomic
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        withdrawal_data = request.session.get('withdrawal_data', None)
        if not withdrawal_data:
            return Response({'error': 'No pending withdrawal data found. please initiate a withdrawal data first'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        account_number = withdrawal_data.get('account_number')
        amount =  Decimal(withdrawal_data.get('amount'))
        try:
            bank_account = BankAccount.objects.get(account_number=account_number, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Invalid account number'}, status=status.HTTP_404_NOT_FOUND)
        
        if bank_account.account_balance < amount:
            return Response({'error': 'Insufficient funds for withdraw'}, status=status.HTTP_400_BAD_REQUEST)
        bank_account.account_balance -= amount
        bank_account.save()

        transaction = Transaction.objects.create(
            user=request.user,
            sender=request.user,
            sender_account=bank_account,
            amount=amount,
            description=f'Withdrawal of {amount} from account {account_number}',
            transaction_type=Transaction.TransactionType.WITHDRAW,
            transaction_status=Transaction.TransactionStatus.SUCCESS
        )
        logger.info(f'Withdrawal of {amount} made from account {account_number} by user {request.user.email}')

        send_withdrawal_email(user=request.user, user_email=request.user.email, amount=amount, 
                              currency=bank_account.account_currency, new_balance=bank_account.account_balance, 
                              account_number=account_number)
        
        del request.session['withdrawal_data']
        
        return Response({
            'message': f'Withdrawal of {amount} completed successfully',
            'transaction': TransactionSerializer(transaction).data,
        }, status=status.HTTP_200_OK)

class InitiateTransferView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'initiate_transfer'

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data.copy()
        data['transaction_type'] = Transaction.TransactionType.TRANSFER
        sender_account_number = data.get('sender_account')
        receiver_account_number = data.get('receiver_account')

        if sender_account_number == receiver_account_number:
            return Response({'error': 'Sender and receiver accounts cannot be the same'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sender_bank_account = BankAccount.objects.get(account_number=sender_account_number, user=request.user)
            BankAccount.objects.get(account_number=receiver_account_number)
            if not (sender_bank_account.fully_activated and sender_bank_account.kyc_verified):
                return Response({'error': 'Sender account isn\'t fully verified'}, status=status.HTTP_403_FORBIDDEN)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Invalid account number'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            request.session['transfer_data'] = {
                'sender_account': sender_account_number,
                'receiver_account': receiver_account_number,
                'amount': str(serializer.validated_data['amount']),
                'description': serializer.validated_data.get('description', '')
            }
            logger.info('Transfer data is saved in session')
            return Response({
                'message': 'Transfer initiated successfully, Please answer the security question to complete the transfer',
                'next_step': 'Verify security question'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifySecurityQuestionAndTransferApiView(generics.CreateAPIView):
    serializer_class = SecurityQuestionSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'verification_answer'

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            otp = generate_otp()
            request.user.set_otp(otp)
            send_transfer_otp_email(email=request.user.email, otp=otp)
            return Response({
                'message': 'Security question verified successfully, Please verify the OTP sent to your email',
                'next_step': 'Verify OTP'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyOTPAndTransferView(generics.CreateAPIView):
    serializer_class = OTPVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'otp_verification'

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return self.process_transfer(request)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def process_transfer(self, request: Request) -> Response:
        transfer_data = request.session.get('transfer_data', None)
        if not transfer_data:
            return Response({'error': 'No pending transfer data found. Please initiate a transfer data first'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            sender_account_number = transfer_data.get('sender_account')
            sender_account = BankAccount.objects.get(account_number=sender_account_number, user=request.user)
            receiver_account_number = transfer_data.get('receiver_account')
            receiver_account = BankAccount.objects.get(account_number=receiver_account_number)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Invalid account number'}, status=status.HTTP_404_NOT_FOUND)
        
        amount = Decimal(transfer_data.get('amount'))
        if sender_account.account_balance < amount:
            return Response({'error': 'Insufficient funds for transfer'}, status=status.HTTP_400_BAD_REQUEST)
        
        sender_account.account_balance -= amount
        receiver_account.account_balance += amount
        sender_account.save()
        receiver_account.save()

        description = transfer_data.get('description', '')
        transaction = Transaction.objects.create(
            user=request.user,
            sender=request.user,
            sender_account=sender_account,
            receiver=receiver_account.user,
            receiver_account=receiver_account,
            amount=amount,
            description=description,
            transaction_type=Transaction.TransactionType.TRANSFER,
            transaction_status=Transaction.TransactionStatus.SUCCESS
        )

        del request.session['transfer_data']

        send_transfer_email(sender=request.user, sender_email=request.user.email, receiver=receiver_account.user,
                            receiver_email=receiver_account.user.email, amount=amount, 
                            currency=sender_account.account_currency, 
                            sender_new_balance=sender_account.account_balance, 
                            receiver_new_balance=receiver_account.account_balance,
                            sender_account_number=sender_account_number, 
                            receiver_account_number=receiver_account_number)
        logger.info(f'Transfer made from account : {sender_account_number} to account : ' +
                    f'{receiver_account_number} by user {request.user.email}')
        
        return Response({
            'message': f'Transfer of {amount} completed successfully',
            'transaction': TransactionSerializer(transaction).data
        }, status=status.HTTP_200_OK)

