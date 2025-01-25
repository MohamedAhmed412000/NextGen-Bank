from typing import Any, List

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, filters, generics, serializers

from core_apps.accounts.utils import create_bank_account
from core_apps.accounts.models import BankAccount
from core_apps.common.models import ContentView
from core_apps.common.permissions import IsBranchManager
from core_apps.common.renderers import GenericJSONRenderer

from .models import UserProfile, NextOfKin
from .serializers import UserProfileSerializer, UserProfileListSerializer, NextOfKinSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserProfileListView(generics.ListAPIView):
    serializer_class = UserProfileListSerializer
    renderer_classes = [GenericJSONRenderer]
    pagination_class = StandardResultsSetPagination
    object_label = 'Profiles'
    permission_classes = [IsBranchManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ('user__first_name', 'user__last_name', 'user__id_no')
    search_fields = ('user__first_name', 'user__last_name', 'user__id_no')

    def get_queryset(self):
        return UserProfile.objects.exclude(user__is_superuser=True).exclude(user__is_staff=True)
    
class UserProfileDetailsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    parser_classes = [FormParser, JSONParser, MultiPartParser]
    renderer_classes = [GenericJSONRenderer]
    object_label = 'Profile Details'

    def get_object(self) -> UserProfile:
        try:
            user_profile = UserProfile.objects.get(user=self.request.user)
            self.record_user_profile(user_profile)
            return user_profile
        except UserProfile.DoesNotExist:
            raise Http404('Profile does not exist')
        
    def record_user_profile(self, user_profile) -> None:
        content_type = ContentType.objects.get_for_model(user_profile)
        viewer_ip = self.get_viewer_ip()
        user = self.request.user

        ContentView.objects.update_or_create(content_type=content_type, object_id=user_profile.id, 
                                                user=user, viewer_ip=viewer_ip, defaults={
                                                    'last_viewed': timezone.now(),
                                                })
        
    def get_viewer_ip(self) -> str:
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        else:
            return self.request.META.get('REMOTE_ADDR')
        
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer: UserProfileSerializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                user_profile: UserProfile = serializer.save()
                if user_profile.is_complete_with_next_of_kin():
                    bank_account = BankAccount.objects.filter(
                        user=user_profile.user, 
                        account_type=user_profile.account_type, 
                        account_currency=user_profile.account_currency).first()
                    if not bank_account:
                        create_bank_account(user_profile.user, account_type=user_profile.account_type, 
                                            account_currency=user_profile.account_currency)
                        message = "User profile updated successfully and a new bank account was created. " + \
                            "An email has been sent for further instructions."
                    else:
                        message = "User profile updated successfully. No new bank account was created. " + \
                            "As the user already has an existing bank account."
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
                else:
                    message = "User profile updated successfully. Please complete the required fields and " + \
                        "add at least one next of kin to create a new bank account."
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def perform_update(self, serializer: UserProfileSerializer) -> None:
        serializer.save()

class NextOfKinApiView(generics.ListCreateAPIView):
    serializer_class = NextOfKinSerializer
    pagination_class = StandardResultsSetPagination
    renderer_classes = [GenericJSONRenderer]
    object_label = 'Next of Kin'

    def get_queryset(self) -> List[NextOfKin]:
        return NextOfKin.objects.filter(profile__user=self.request.user)
    
    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context['profile'] = self.request.user.profile
        return context
    
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer: NextOfKinSerializer) -> None:
        serializer.save()

class NextOfKinDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NextOfKinSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = 'Next of Kin'

    def get_queryset(self) -> List[NextOfKin]:
        return NextOfKin.objects.filter(profile__user=self.request.user)
    
    def get_object(self) -> NextOfKin:
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk = self.kwargs['pk'])
        self.check_object_permissions(self.request, obj) 
        return obj

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer: NextOfKinSerializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer: NextOfKinSerializer) -> None:
        serializer.save()
    
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Next of kin deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    def perform_destroy(self, instance: NextOfKin) -> None:
        instance.delete()
