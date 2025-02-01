from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel
from core_apps.accounts.models import BankAccount

User = get_user_model()

class VirtualCard(TimeStampedModel):
    class CardStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        IN_ACTIVE = 'IN_ACTIVE', _('Inactive')
        EXPIRED = 'EXPIRED', _('Expired')
        LOCKED = 'LOCKED', _('Locked')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='virtual_cards')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='virtual_cards')
    card_number = models.CharField(max_length=16, unique=True, db_index=True)
    expiry_date = models.DateTimeField()
    cvv = models.CharField(max_length=3)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    card_status = models.CharField(max_length=10, choices=CardStatus.choices, default=CardStatus.ACTIVE)

    def __str__(self):
        return f'Virtual card {self.card_number} for {self.user.full_name}'
