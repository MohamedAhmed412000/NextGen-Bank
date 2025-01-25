# Generated by Django 4.2.15 on 2025-01-25 06:41

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="account_currency",
            field=models.CharField(
                blank=True,
                choices=[
                    ("EGP", "EGP"),
                    ("SAR", "SAR"),
                    ("USD", "USD"),
                    ("EUR", "EUR"),
                ],
                max_length=10,
                null=True,
                verbose_name="Account Currency",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="account_type",
            field=models.CharField(
                blank=True,
                choices=[("CURRENT", "Current"), ("SAVING", "Saving")],
                max_length=10,
                null=True,
                verbose_name="Account Type",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                default="+201078412345",
                max_length=30,
                region=None,
                verbose_name="Phone Number",
            ),
        ),
    ]
