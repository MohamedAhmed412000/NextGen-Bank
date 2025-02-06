from typing import List
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger

from .models import BankAccount

def send_account_creation_email(user: 'User', bank_account: BankAccount) -> None:
    subject = _('You new bank account has been created')
    context = {
        'user': user,
        'account': bank_account,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/account_created.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    try:
        msg.send()
        logger.info(f'Account created email sent to {user.email}')
    except Exception as e:
        logger.error(f'Failed to send account created email to {user.email}, Error: {e}')

def send_full_activation_email(bank_account: BankAccount) -> None:
    subject = _('Your bank account is now fully activated')
    context = {
        'account': bank_account,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/bank_account_activated.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [bank_account.user.email]
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    try:
        msg.send()
        logger.info(f'Account activation email sent to {bank_account.user.email}')
    except Exception as e:
        logger.error(f'Failed to send account activated email to {bank_account.user.email}, Error: {e}')

def send_deposite_email(user, user_email, amount, currency, new_balance, account_number) -> None:
    subject = _('Deposit Confirmation')
    context = {
        'user': user,
        'amount': amount,
        'currency': currency,
        'new_balance': new_balance,
        'account_number': account_number,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/deposit_confirmation.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    try:
        msg.send()
        logger.info(f'Deposit confirmation email sent to {user_email}')
    except Exception as e:
        logger.error(f'Failed to send deposit confirmation email to {user_email}, Error: {e}')

def send_withdrawal_email(user, user_email, amount, currency, new_balance, account_number) -> None:
    subject = _('Withdrawal Confirmation')
    context = {
        'user': user,
        'amount': amount,
        'currency': currency,
        'new_balance': new_balance,
        'account_number': account_number,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/withdraw_confirmation.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    try:
        msg.send()
        logger.info(f'Withdrawal confirmation email sent to {user_email}')
    except Exception as e:
        logger.error(f'Failed to send withdrawal confirmation email to {user_email}, Error: {e}')

def send_transfer_email(sender, sender_email, receiver, receiver_email, amount, currency, 
                sender_new_balance, receiver_new_balance, sender_account_number, receiver_account_number) -> None:
    from_email = settings.DEFAULT_FROM_EMAIL
    subject = _('Transfer Notification')
    common_context = {
        'amount': amount,
        'currency': currency,
        'sender_account_number': sender_account_number,
        'receiver_account_number': receiver_account_number,
        'sender_name': sender.full_name,
        'receiver_name': receiver.full_name,
        'site_name': settings.SITE_NAME,
    }
    
    # Send notification email to sender
    sender_context = {
        **common_context,
        'user': sender,
        'is_sender': True,
        'new_balance': sender_new_balance,
    }
    html_content = render_to_string('emails/transfer_notification.html', sender_context)
    text_content = strip_tags(html_content)
    sender_msg = EmailMultiAlternatives(subject, text_content, from_email, [sender_email])
    sender_msg.attach_alternative(html_content, 'text/html')

    # Send confirmation email to receiver
    receiver_context = {
        **common_context,
        'user': receiver,
        'is_sender': False,
        'new_balance': receiver_new_balance,
    }
    html_content = render_to_string('emails/transfer_notification.html', receiver_context)
    text_content = strip_tags(html_content)
    receiver_msg = EmailMultiAlternatives(subject, text_content, from_email, [receiver_email])
    receiver_msg.attach_alternative(html_content, 'text/html')
    try:
        sender_msg.send()
        receiver_msg.send()
        logger.info(f'Transfer notification email sent to sender: {sender_email} and receiver: {receiver_email}')
    except Exception as e:
        logger.error(f'Failed to send transfer notification emails, Error: {e}')


def send_transfer_otp_email(email, otp):
    subject = _('Your OTP for Transfer Authorization')
    context = {
        'otp': otp,
        'expiry_time': settings.OTP_EXPIRATION,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/transfer_otp_email.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    try:
        msg.send()
        logger.info(f'OTP email sent successfully to {email}')
    except Exception as e:
        logger.error(f'Failed to send OTP email to {email}, Error: {e}')

def send_transaction_pdf(user, start_date, end_date, pdf) -> None:
    subject = _('Your translations history PDF')
    context = {
        'user': user,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/transactions_history_pdf.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, 'text/html')
    email.attach(f'transactions_from_{start_date}_to_{end_date}.pdf', pdf, 'application/pdf')

    try:
        email.send()
        logger.info(f'Transaction history PDF email sent to {user.email}')
    except Exception as e:
        logger.error(f'Failed to send transaction history PDF email to {user.email}, Error: {str(e)}')

def send_suspicious_activity_alert(suspicious_activities: List[str]) -> int:
    subject = _('Suspicious Activity Alert')
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.ADMIN_EMAIL]
    context = {
        'suspicious_activities': suspicious_activities,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/suspicious_activity_alert.html', context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send()
        logger.info(f'Suspicious activity alert email sent to {settings.ADMIN_EMAIL}')
        return len(suspicious_activities)
    except Exception as e:
        logger.error(f'Failed to send suspicious activity alert email, Error: {str(e)}')
        return 0
