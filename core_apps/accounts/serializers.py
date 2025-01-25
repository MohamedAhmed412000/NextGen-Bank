from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

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
