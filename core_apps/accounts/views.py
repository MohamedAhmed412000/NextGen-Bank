from typing import Any

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from core_apps.common.permissions import IsAccountExecutive
from core_apps.common.renderers import GenericJSONRenderer

from .models import BankAccount
from .serializers import BankAccountVerificationSerializer
from .emails import send_full_activation_email

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
                instance.account_status = str(BankAccount.AccountStatus.ACTIVE.label)
                instance.save()

                send_full_activation_email(instance)
            return Response({
                'message': 'Account verification status updated successfully',
                'data': self.get_serializer(instance).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

