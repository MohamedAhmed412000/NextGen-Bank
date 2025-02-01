from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import BankAccount, Transaction

User = get_user_model()

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'user', 'account_currency', 'account_type', 'account_balance', 
                    'account_status', 'is_primary', 'kyc_verified', 'get_verified_by']
    list_filter = ['account_currency', 'account_type', 'account_status', 'is_primary', 'kyc_submitted', 
                   'kyc_verified']
    search_fields = ['account_number', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'account_number', 'account_balance', 'account_currency', 'account_type', 'is_primary')
        }),
        (_('Status'), {
            'fields': ('account_status', 'kyc_submitted', 'kyc_verified', 'verification_date', 'fully_activated', 
                       'verification_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_verified_by(self, obj: BankAccount) -> str:
        return obj.verified_by.full_name if obj.verified_by else '-'
    
    get_verified_by.short_description = _('Verified By')
    get_verified_by.admin_order_field = 'verified_by__first_name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(verified_by=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.is_superuser or obj.verified_by == request.user
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'verified_by':
            kwargs['queryset'] = User.objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender_full_name', 'receiver_full_name', 'transaction_type', 'description', 'amount', 
                    'transaction_currency', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['sender_full_name','receiver_full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (_('Transaction Details'), {
            'fields': ('id', 'transaction_type', 'description', 'amount', 'transaction_status')
        }),
        (_('Sender Section'), {
            'fields': ('sender', 'sender_account')
        }),
        (_('Receiver Section'), {
            'fields': ('receiver','receiver_account')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)
        }),
    )

    def transaction_currency(self, obj):
        return obj.sender_account.account_currency if obj.sender_account else obj.receiver_account.account_currency
    
    transaction_currency.short_description = _('Currency')

    def sender_full_name(self, obj):
        return obj.sender.full_name if obj.sender else 'N/A'
    
    sender_full_name.short_description = _('Sender')
    sender_full_name.admin_order_field ='sender__first_name'

    def receiver_full_name(self, obj):
        return obj.receiver.full_name if obj.receiver else 'N/A'
    
    receiver_full_name.short_description = _('Receiver')
    receiver_full_name.admin_order_field ='receiver__first_name'

    def has_delete_permission(self, request, obj = ...):
        return False
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
