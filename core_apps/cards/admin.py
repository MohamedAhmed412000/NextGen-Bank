from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import VirtualCard

@admin.register(VirtualCard)
class VirtualCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'user_full_name', 'bank_account_number', 'expiry_date', 'balance', 
                    'card_status']
    list_filter = ['card_status', 'expiry_date']
    search_fields = ['card_number', 'user__email', 'user__first_name', 'user__last_name', 'account__account_number']
    readonly_fields = ['card_number', 'cvv', 'created_at', 'updated_at']
    fieldsets = (
        (_('Card Info'), {
            'fields': ('user', 'account', 'card_number', 'cvv', 'expiry_date')
        }),
        (_('Card Details'), {
            'fields': ('balance', 'card_status')
        }),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse')})
    )

    def user_full_name(self, obj):
        return obj.user.full_name
    
    user_full_name.short_description = _('User')
    user_full_name.admin_order_field = 'user__first_name'

    def bank_account_number(self, obj):
        return obj.account.account_number
    
    bank_account_number.short_description = _('Bank Account Number')
    bank_account_number.admin_order_field = 'account__account_number'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'account')

    def has_delete_permission(self, request, obj = ...) -> bool:
        return False
