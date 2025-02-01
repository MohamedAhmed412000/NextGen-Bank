from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import VirtualCard
from .utils import generate_card_number, generate_card_cvv

class UUIDField(serializers.Field):
    def to_representation(self, value: str) -> str:
        return str(value)
    
class VirtualCardSerializer(serializers.ModelSerializer):
    id = UUIDField(read_only=True)
    balance = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal('0.01')
    )

    class Meta:
        model = VirtualCard
        fields = ['id', 'card_number', 'expiry_date', 'cvv', 'balance', 'card_status']
        read_only_fields = ['id', 'card_number', 'expiry_date', 'cvv']

class VirtualCardCreateSerializer(serializers.ModelSerializer):
    bank_account_number = serializers.CharField(write_only=True)

    class Meta:
        model = VirtualCard
        fields = ['bank_account_number']

    def validate(self, attrs):
        user = self.context['request'].user
        if user.virtual_cards.count() >= 3:
            return serializers.ValidationError('You can only have up to 3 virtual cards at a time')
        return attrs
    
    def create(self, validated_data: dict) -> VirtualCard:
        user = validated_data.get('user')
        bank_account_number = validated_data.pop('bank_account_number')

        bank_account = user.bank_accounts.get(account_number = bank_account_number)
        if not bank_account:
            return serializers.ValidationError('Invalid bank account number')
        
        card_number = generate_card_number()
        expiry_date = timezone.now() + timezone.timedelta(days=365*3)
        cvv = generate_card_cvv(card_number, expiry_date.strftime('%m/%y'))

        virtual_card = VirtualCard.objects.create(
            user=user,
            account=bank_account,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
        )
        return virtual_card

