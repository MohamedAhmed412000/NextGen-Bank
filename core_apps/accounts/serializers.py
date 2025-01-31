from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from decimal import Decimal

from .models import BankAccount, Transaction

class BankAccountVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['kyc_submitted', 'kyc_verified', 'verification_date', 'verification_notes',
                   'fully_activated', 'account_status']
        read_only_fields = ['fully_activated']
    
    def validate(self, data: dict) -> dict:
        kyc_verified = data.get('kyc_verified')
        kyc_submitted = data.get('kyc_submitted')
        verification_date = data.get('verification_date')
        verification_notes = data.get('verification_notes')
        if kyc_verified:
            if not verification_date:
                raise serializers.ValidationError(_('Verification date is required when KYC is verified'))
            if not verification_notes:
                raise serializers.ValidationError(_('Verification notes are required when KYC is verified'))
        if kyc_submitted and not all([kyc_verified, verification_date, verification_notes]):
            raise serializers.ValidationError(_('All verification fields (KYC Verified, Verification Date, ' + \
                                                'Verification Notes) are required when KYC is submitted'))
        return data
    
    def to_representation(self, instance: BankAccount) -> dict:
        representation = super().to_representation(instance)
        representation['account_status'] = str(instance.account_status.label)
        return representation
    
class DepositSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.1'))

    class Meta:
        model = BankAccount
        fields = ['account_number', 'amount']
    
    def validate_account_number(self, account_number: str) -> str:
        try:
            bank_account = BankAccount.objects.get(account_number=account_number)
            self.context['account'] = bank_account
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(_('Invalid account number'))
        if not bank_account.fully_activated:
            raise serializers.ValidationError(_('Account is not fully activated'))
        return account_number
    
    def to_representation(self, instance: BankAccount) -> str:
        representation = super().to_representation(instance)
        representation['amount'] = str(representation['amount'])
        return representation
    
class CustomerInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name')
    email = serializers.EmailField(source='user.email')
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BankAccount
        fields = ['account_number', 'full_name', 'email', 'photo_url', 'account_balance', 'account_type', 
                  'account_currency']
    
    def get_photo_url(self, instance: BankAccount) -> None:
        if hasattr(instance.user, 'profile') and instance.user.profile.photo_url:
            return instance.user.profile.photo_url
        return None
    
class UUIDField(serializers.Field):
    def to_representation(self, value: str) -> str:
        return str(value)
    
class TransactionSerializer(serializers.ModelSerializer):
    id = UUIDField(read_only=True)
    sender_account = serializers.CharField(max_length=20, required=False)
    receiver_account = serializers.CharField(max_length=20, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.1'))

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'description', 'transaction_status', 'transaction_type', 'created_at',
                  'sender', 'receiver', 'sender_account', 'receiver_account']
        read_only_fields = ['id', 'transaction_status', 'created_at']

    def to_representation(self, instance: Transaction) -> str:
        representation = super().to_representation(instance)
        representation['amount'] = str(representation['amount'])
        representation['sender'] = instance.sender.full_name if instance.sender else None
        representation['receiver'] = instance.receiver.full_name if instance.receiver else None
        representation['sender_account'] = instance.sender_account.account_number if instance.sender_account \
            else None
        representation['receiver_account'] = instance.receiver_account.account_number if instance.receiver_account \
            else None
        return representation

    def validate(self, attrs: dict) -> dict:
        transaction_type = attrs.get('transaction_type')
        sender_account_number = attrs.get('sender_account')
        receiver_account_number = attrs.get('receiver_account')
        amount = attrs.get('amount')
        try:
            if transaction_type == Transaction.TransactionType.WITHDRAW:
                sender_account = BankAccount.objects.get(account_number=sender_account_number)
                attrs['sender_account'] = sender_account
                attrs['receiver_account'] = None
                if sender_account.account_balance < amount:
                    raise serializers.ValidationError(_('Insufficient balance'))
            elif transaction_type == Transaction.TransactionType.DEPOSIT:
                receiver_account = BankAccount.objects.get(account_number=receiver_account_number)
                attrs['sender_account'] = None
                attrs['receiver_account'] = receiver_account
            else:
                sender_account = BankAccount.objects.get(account_number=sender_account_number)
                receiver_account = BankAccount.objects.get(account_number=receiver_account_number)
                attrs['sender_account'] = sender_account
                attrs['receiver_account'] = receiver_account
                if sender_account == receiver_account:
                    raise serializers.ValidationError(_('Sender and receiver accounts cannot be the same'))
                if sender_account.account_currency != receiver_account.account_currency:
                    raise serializers.ValidationError(_('Sender and receiver accounts must have the same currency'))
                if sender_account.account_balance < amount:
                    raise serializers.ValidationError(_('Insufficient balance'))
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(_('Invalid account number'))
        return attrs
    
class SecurityQuestionSerializer(serializers.Serializer):
    security_answer = serializers.CharField(max_length=30)

    def validate(self, attrs: dict) -> dict:
        user = self.context['request'].user
        security_answer = attrs.get('security_answer')
        if security_answer != user.security_answer:
            raise serializers.ValidationError(_('Incorrect security answer'))
        return attrs

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs: dict) -> dict:
        user = self.context['request'].user
        otp = attrs.get('otp')
        if not user.verify_otp(otp):
            raise serializers.ValidationError(_('Invalid or expired OTP'))
        return attrs

class UsernameVerificationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=12)

    def validate(self, attrs: dict) -> dict:
        user = self.context['request'].user
        username = attrs.get('username')
        if user.username != username:
            raise serializers.ValidationError(_('Invalid username'))
        return attrs