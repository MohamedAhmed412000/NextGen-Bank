from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger

def send_account_creation_email(user, bank_account):
    subject = _("You new bank account has been created")
    context = {
        "user": user,
        "account": bank_account,
        "site_name": settings.SITE_NAME,
    }
    html_content = render_to_string("emails/account_created.html", context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        logger.info(f"Account created email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send account created email to {user.email}, Error: {e}")
