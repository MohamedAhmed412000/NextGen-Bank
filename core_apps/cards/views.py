from decimal import Decimal, InvalidOperation
from typing import Any
from django.db import transaction
from loguru import logger

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from core_apps.accounts.models import Transaction
from core_apps.common.renderers import GenericJSONRenderer

from .emails import send_virtual_card_topup_email
from .models import VirtualCard
from .serializers import VirtualCardSerializer, VirtualCardCreateSerializer

class VirtualCardListCreateApiView(generics.ListCreateAPIView):
    renderer_classes = [GenericJSONRenderer]
    object_label = 'visa_card'

    def get_queryset(self) -> VirtualCard:
        return VirtualCard.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VirtualCardCreateSerializer
        return VirtualCardSerializer
    
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.user.virtual_cards.count() >= 3:
            return Response({
                'error': 'You cannot create more than 3 virtual cards at a time.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        bank_account_number = serializer.validated_data.get('bank_account_number')
        user_bank_accounts = request.user.bank_accounts.all()
        if not user_bank_accounts.filter(account_number = bank_account_number).exists():
            return Response({
                'error': 'The provided bank account number is not associated with your account.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        virtual_card = serializer.save(user = request.user)
        logger.info(f'Visa card number {virtual_card.card_number} created for user {request.user.full_name}')
        return Response(VirtualCardSerializer(virtual_card).data, status=status.HTTP_201_CREATED)

class VirtualCardApiView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VirtualCardSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'visa_card'

    def get_queryset(self):
        return VirtualCard.objects.filter(user=self.request.user)
    
    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('You do not have permission to access this virtual card.')
        return obj

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            virtual_card = self.get_object()
            if virtual_card.balance > 0:
                return Response({
                    'error': 'Cannot delete a virtual card with remaining balance.'
                }, status=status.HTTP_400_BAD_REQUEST)
            virtual_card.delete()
            logger.info(f'Visa card number {virtual_card.card_number} deleted for user {request.user.full_name}')
            return Response({
                'message': 'Visa card deleted successfully'
            }, status=status.HTTP_200_OK)
        except VirtualCard.DoesNotExist:
            return Response({'error': 'Virtual card not found.'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f'Error deleting virtual card: {str(e)}')
            return Response({'error': 'An error occurred while deleting the virtual card.'}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VirtualCardTopupApiView(generics.UpdateAPIView):
    renderer_classes = [GenericJSONRenderer]
    object_label = 'visa_card'

    def get_queryset(self):
        return VirtualCard.objects.filter(user=self.request.user)
    
    @transaction.atomic
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        virtual_card = self.get_object()
        amount = request.data.get('amount')
        if not amount:
            return Response({
                'error': 'Top-up amount is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            amount = Decimal(amount)
        except InvalidOperation:
            return Response({
                'error': 'Top-up amount must be a valid decimal number.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if amount <= 0:
            return Response({
                'error': 'Top-up amount must be greater than zero.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        bank_account = virtual_card.account
        if bank_account.account_balance < amount:
            return Response({
                'error': 'Insufficient funds for top-up.'
            }, status=status.HTTP_400_BAD_REQUEST)

        bank_account.account_balance -= amount
        virtual_card.balance += amount
        bank_account.save()
        virtual_card.save()

        Transaction.objects.create(
            user=request.user,
            amount=amount,
            description=f'Top-up for Visa Card ending in {virtual_card.card_number[-4:]}',
            transaction_type=Transaction.TransactionType.DEPOSIT,
            transaction_status=Transaction.TransactionStatus.SUCCESS,
            sender=request.user,
            receiver=request.user,
            sender_account=bank_account,
            receiver_account=bank_account
        )
        
        send_virtual_card_topup_email(request.user, virtual_card.card_number, amount, bank_account.account_currency,
                                       virtual_card.balance)
        logger.info(f'Top-up of {amount} to virtual card number {virtual_card.card_number} ' + \
                    f'for user {request.user.full_name}')
        
        return Response(VirtualCardSerializer(virtual_card).data, status=status.HTTP_200_OK)
