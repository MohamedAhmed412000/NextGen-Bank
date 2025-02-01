from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from loguru import logger

def send_virtual_card_topup_email(user, card_number, amount, currency, new_balance):
    subject = 'Virtual Card Top-up Confirmation'
    context = {
        'user': user,
        'card_last_four': card_number[-4:],
        'amount': amount,
        'currency': currency,
        'new_balance': new_balance,
        'site_name': settings.SITE_NAME,
    }
    html_content = render_to_string('emails/virtual_card_topup.html', context)
    text_content = strip_tags(html_content)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send()
        logger.info(f'Virtual card top-up email sent successfully to {user.email}')
    except Exception as e: 
        logger.error(f'Failed to send virtual card top-up email to {user.email}, Error: {str(e)}')
