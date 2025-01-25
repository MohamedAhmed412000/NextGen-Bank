from typing import Any

from cloudinary.models import CloudinaryField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from core_apps.common.models import TimeStampedModel
from core_apps.accounts.models import BankAccount

User = get_user_model()

class UserProfile(TimeStampedModel):
    class Salutation(models.TextChoices):
        MR = 'MR', _('Mr')
        MRS = 'MRS.', _('Mrs')
        MISS = 'MISS', _('Miss')

    class Gender(models.TextChoices):
        MALE = 'MALE', _('Male')
        FEMALE = 'FEMALE', _('Female')

    class MartialStatus(models.TextChoices):
        SINGLE = 'SINGLE', _('Single')
        MARRIED = 'MARRIED', _('Married')
        DIVORCED = 'DIVORCED', _('Divorced')
        WIDOWED = 'WIDOWED', _('Widowed')
        SEPARATED = 'SEPARATED', _('Separated')
        UNKNOWN = 'UNKNOWN', _('Unknown')

    class IdentificationType(models.TextChoices):
        NATIONAL_ID = 'NATIONAL_ID', _('National ID')
        PASSPORT = 'PASSPORT', _('Passport')
        DRIVING_LICENSE = 'DRIVING_LICENSE', _('Driving License')
        
    class EmploymentStatus(models.TextChoices):
        EMPLOYED = 'EMPLOYED', _('Employed')
        UNEMPLOYED = 'UNEMPLOYED', _('Unemployed')
        SELF_EMPLOYED = 'SELF_EMPLOYED', _('Self Employed')
        RETIRED = 'RETIRED', _('Retired')
        STUDENT = 'STUDENT', _('Student')

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    title = models.CharField(_('Salutation'), max_length=5, choices=Salutation.choices, default=Salutation.MR)
    gender = models.CharField(_('Gender'), max_length=7, choices=Gender.choices, default=Gender.MALE)
    date_of_birth = models.DateField(_('Date of Birth'), default=settings.DEFAULT_BIRTH_DATE)
    country_of_birth = CountryField(_('Country of Birth'), default=settings.DEFAULT_COUNTRY)
    place_of_birth = models.CharField(_('Place of Birth'), max_length=50, default='Unknown')
    martial_status = models.CharField(_('Martial Status'), max_length=10, choices=MartialStatus.choices, 
                            default=MartialStatus.UNKNOWN.name)
    identification_type = models.CharField(_('Identification Type'), max_length=16, 
                            choices=IdentificationType.choices, default=IdentificationType.NATIONAL_ID)
    id_issue_date = models.DateField(_('ID or Passport Issue Date'), default=settings.DEFAULT_DATE)
    id_expiry_date = models.DateField(_('ID or Passport Expiry Date'), default=settings.DEFAULT_EXPIRY_DATE)
    passport_number = models.CharField(_('Passport Number'), max_length=20, blank=True, null=True)
    nationality = models.CharField(_('Nationality'), max_length=30, default='Unknown')
    phone_number = PhoneNumberField(_('Phone Number'), max_length=30, default=settings.DEFAULT_PHONE_NUMBER)
    
    address = models.CharField(_('Address'), max_length=100, default='Unknown')
    city = models.CharField(_('City'), max_length=50, default='Unknown')
    country = CountryField(_('Country'), default=settings.DEFAULT_COUNTRY)
    
    employment_status = models.CharField(_('Employment Status'), max_length=13, 
                                choices=EmploymentStatus.choices, default=EmploymentStatus.SELF_EMPLOYED)
    employer_name = models.CharField(_('Employer Name'), max_length=50, blank=True, null=True)
    annual_income = models.DecimalField(_('Annual Income'), max_digits=12, decimal_places=2, default=0.00)
    date_of_employment = models.DateField(_('Date of Employment'), blank=True, null=True)
    employer_address = models.CharField(_('Employer Address'), max_length=100, blank=True, null=True)
    employer_city = models.CharField(_('Employer City'), max_length=50, blank=True, null=True)
    employer_state = models.CharField(_('Employer State'), max_length=50, blank=True, null=True)
    account_currency = models.CharField(_('Account Currency'), max_length=10, null=True, blank=True,
                                        choices=BankAccount.AccountCurrency.choices)
    account_type = models.CharField(_('Account Type'), max_length=10, null=True, blank=True,
                                        choices=BankAccount.BankAccountType.choices)
    
    photo = CloudinaryField(_('Photo'), blank=True, null=True)
    photo_url = models.URLField(_('Photo URL'), blank=True, null=True)

    id_photo = CloudinaryField(_('ID Photo'), blank=True, null=True)
    id_photo_url = models.URLField(_('ID Photo URL'), blank=True, null=True)

    signature_photo = CloudinaryField(_('Signature Photo'), blank=True, null=True)
    signature_photo_url = models.URLField(_('Signature Photo URL'), blank=True, null=True)

    def clean(self) -> None:
        super().clean()
        if self.id_issue_date and self.id_expiry_date:
            if self.id_expiry_date <= self.id_issue_date:
                raise ValidationError({'id_expiry_date': _('Expiry date must be after issue date.')})
            
    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def is_complete_with_next_of_kin(self):
        required_fields = [
            self.title, self.gender, self.date_of_birth, self.country_of_birth, self.place_of_birth, 
            self.martial_status, self.identification_type, self.id_issue_date, self.id_expiry_date, 
            self.nationality, self.phone_number, self.address, self.city, self.country, self.photo, 
            self.id_photo, self.signature_photo
        ]
        return all(required_fields) and self.next_of_kin.exists()
    
    def __str__(self) -> str:
        return f'{self.title} {self.user.first_name}\'s Profile'
    
class NextOfKin(TimeStampedModel):
    class Salutation(models.TextChoices):
        MR = 'MR', _('Mr')
        MRS = 'MRS.', _('Mrs')
        MISS = 'MISS', _('Miss')

    class Gender(models.TextChoices):
        MALE = 'MALE', _('Male')
        FEMALE = 'FEMALE', _('Female')

    profile = models.ForeignKey(UserProfile, related_name='next_of_kin', on_delete=models.CASCADE)
    title = models.CharField(_('Salutation'), max_length=5, choices=Salutation.choices, default=Salutation.MR)
    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    other_names = models.CharField(_('Other Names'), max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(_('Date of Birth'))
    gender = models.CharField(_('Gender'), max_length=7, choices=Gender.choices)
    relationship = models.CharField(_('Relationship'), max_length=50)
    email_address = models.EmailField(_('Email Address'), db_index=True)
    phone_number = PhoneNumberField(_('Phone Number'))
    address = models.CharField(_('Address'), max_length=100)
    city = models.CharField(_('City'), max_length=50)
    country = CountryField(_('Country'))
    is_primary = models.BooleanField(_('Is Primary Next Of Kin'), default=False)

    def clean(self) -> None:
        super().clean()
        if self.is_primary:
            primary_kin = NextOfKin.objects.filter(profile=self.profile, is_primary=True).exclude(pk=self.pk)
            if primary_kin.exists():
                raise ValidationError(_('Primary Next of Kin already exists for this profile.'))

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name} - Next of Kin for {self.profile.user.first_name}'
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'is_primary'], 
                condition=models.Q(is_primary=True), 
                name='unique_primary_next_of_kin'
            )
        ]