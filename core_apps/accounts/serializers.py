from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from decimal import Decimal

from .models import BankAccount

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

