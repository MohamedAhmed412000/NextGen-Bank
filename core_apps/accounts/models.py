from typing import Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP
from loguru import logger

from core_apps.common.models import TimeStampedModel

User = get_user_model()

class BankAccount(TimeStampedModel):
    class BankAccountType(models.TextChoices):
        CURRENT = 'CURRENT', _('Current')
        SAVING = 'SAVING', _('Saving')

    class AccountStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'IN_ACTIVE', _('In-active')

    class AccountCurrency(models.TextChoices):
        EGP = 'EGP', _('EGP')
        SAR = 'SAR', _('SAR')
        USD = 'USD', _('USD')
        EUR = 'EUR', _('EUR')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(_('Account Number'), max_length=20, unique=True)
    account_balance = models.DecimalField(_('Account Balance'), max_digits=10, decimal_places=2, default=0.00)
    account_type = models.CharField(_('Account Type'), max_length=10, choices=BankAccountType.choices, 
                                    default=BankAccountType.CURRENT)
    account_status = models.CharField(_('Account Status'), max_length=10, choices=AccountStatus.choices, 
                                    default=AccountStatus.INACTIVE)
    account_currency = models.CharField(_('Account Currency'), max_length=3, choices=AccountCurrency.choices,
                                    default=AccountCurrency.EGP)
    is_primary = models.BooleanField(_('Is Primary'), default=False)
    kyc_submitted = models.BooleanField(_('KYC Submitted'), default=False)
    kyc_verified = models.BooleanField(_('KYC Verified'), default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='verified_accounts', 
                                    null=True, blank=True)
    verification_date = models.DateTimeField(_('Verification Date'), null=True, blank=True)
    verification_notes = models.TextField(_('Verification Notes'), null=True, blank=True)
    fully_activated = models.BooleanField(_('Fully Activated'), default=False)
    interest_rate = models.DecimalField(_('Interest Rate'), max_digits=5, decimal_places=4, default=0.00, 
                                        help_text='Annual interest rate as a decimal (eg. 0.0150 for 1.50%)')

    def __str__(self) -> str:
        return f'{self.user.full_name}\'s {self.get_account_currency_display()} - {self.get_account_type_display()} ' + \
            f'Account - {self.account_number}'
    
    @property
    def annual_interest_rate(self):
        if self.account_type != BankAccount.BankAccountType.SAVING:
            return Decimal(0)
        balance = Decimal(self.account_balance)
        if balance < Decimal(100000):
            return Decimal(0.0050)
        elif Decimal(100000) <= balance < Decimal(500000):
            return Decimal(0.0100)
        else:
            return Decimal(0.0150)
        
    def apply_daily_interest(self) -> Decimal:
        if self.account_type == BankAccount.BankAccountType.SAVING:
            daily_rate = self.annual_interest_rate / Decimal(365)
            interest = (daily_rate * Decimal(self.account_balance)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            logger.info(f'Applying daily interest {interest} to account {self.account_type}')
            self.account_balance += interest
            self.save()

            Transaction.objects.create(
                user=self.user,
                amount=interest,
                transaction_type=Transaction.TransactionType.INTEREST,
                description=f'Daily interest applied for account {self.account_number}',
                receiver=self.user,
                receiver_account=self,
                transaction_status=Transaction.TransactionStatus.SUCCESS,
            )
            return interest
        return Decimal(0.00)

    class Meta:
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        unique_together = ('user', 'account_currency', 'account_type')

    def clean(self) -> None:
        if self.account_balance < 0:
            raise ValidationError(_('Account balance cannot be negative.'))

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.is_primary:
            BankAccount.objects.filter(user=self.user).update(is_primary=False)
        super().save(*args, **kwargs)


class Transaction(TimeStampedModel):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', _('Deposit')
        WITHDRAW = 'WITHDRAW', _('Withdraw')
        TRANSFER = 'TRANSFER', _('Transfer')
        INTEREST = 'INTEREST', _('Interest')

    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SUCCESS = 'SUCCESS', _('Success')
        FAILED = 'FAILED', _('Failed')

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transactions')
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2, default=0.00)
    description = models.TextField(_('Description'), null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_transactions')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_transactions')
    receiver_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, 
                                        related_name='received_transactions')
    sender_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, 
                                        related_name='sent_transactions')
    transaction_type = models.CharField(_('Transaction Type'), max_length=10, choices=TransactionType.choices)
    transaction_status = models.CharField(_('Transaction Status'), max_length=10, choices=TransactionStatus.choices,
                                        default=TransactionStatus.PENDING)
    
    def __str__(self) -> str:
        return f'{self.transaction_type} - {self.amount} - {self.transaction_status}'

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        indexes = [
            models.Index(fields=['created_at']),
        ]
        