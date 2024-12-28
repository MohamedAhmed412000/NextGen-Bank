from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger

def send_otp_email(email, otp) -> None:
    subject = _('Your OTP code for login')
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    context = {
        'otp': otp,
        'expiry_time': settings.OTP_EXPIRATION,
        'site_name': settings.SITE_NAME
    }
    html_content = render_to_string('emails/otp_email.html', context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send()
        logger.info(f'OTP email sent successfully to {email}')
    except Exception as e:
        logger.error(f'Failed to send OTP email to {email}: Error: {str(e)}')

def send_account_locked_email(self) -> None:
    subject = _('Your account has been locked')
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [self.email]
    context = {
        'user': self,
        'lockout_duration': int(settings.LOCKOUT_DURATION.total_seconds() // 60),
        'site_name': settings.SITE_NAME
    }
    html_content = render_to_string('emails/account_locked_email.html', context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send()
        logger.info(f'Account locked email sent successfully to {self.email}')
    except Exception as e:
        logger.error(f'Failed to send account locked email to {self.email}: Error: {str(e)}')