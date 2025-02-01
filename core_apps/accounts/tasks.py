from io import BytesIO

from celery import shared_task
from dateutil import parser
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from loguru import logger

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core_apps.accounts.models import BankAccount, Transaction

from .emails import send_transaction_pdf

User = get_user_model()

@shared_task
def generate_transactions_PDF(user_id: str, start_date: str, end_date: str, account_number: str = None) -> None:
    try:
        user = User.objects.get(id=user_id)
        start_date = parser.parse(start_date).date()
        end_date = parser.parse(end_date).date()
        transactions = Transaction.objects.filter(
            Q(sender=user) | Q(receiver=user),
            created_at__date__range=[start_date, end_date]
        )

        if account_number:
            account = BankAccount.objects.get(account_number=account_number, user=user)
            transactions = transactions.filter(Q(sender_account=account) | Q(receiver_account=account))

        transactions = transactions.order_by('-created_at')
        pdf = generate_PDF(start_date, end_date, transactions)
        send_transaction_pdf(user, start_date, end_date, pdf)
        return f'PDF generated and sent to {user.email}'
    except Exception as e:
        logger.error(f'Failed to generate transactions PDF for user {user_id}, Error: {str(e)}')
        return f'Failed to generate transactions PDF: {str(e)}'

def generate_PDF(start_date, end_date, transactions: list[Transaction]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, 
                            bottomMargin=18)
    styles = getSampleStyleSheet()
    
    elements = []
    header = Paragraph(f'Transaction History from {start_date} to {end_date}', styles['Title'])
    elements.append(header)
    elements.append(Spacer(1, 12))

    data = []
    data.append(['Date', 'Type', 'Amount', 'Description', 'Status', 'Sender', 'Receiver'])
    for transaction in transactions:
        data.append([
            transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.get_transaction_type_display(),
            f'{transaction.amount:.2f} {get_account_currency(transaction)}',
            transaction.description[:30] + '...' if len(transaction.description) > 30 else transaction.description,
            transaction.get_transaction_status_display(),
            transaction.sender.get_full_name() if transaction.sender else 'N/A',
            transaction.receiver.get_full_name() if transaction.receiver else 'N/A'
        ])

    col_widths = [1.8 * inch, 1.2 * inch, 1.2 * inch, 2.5 * inch, 1.2 * inch, 1.5 * inch, 1.5 * inch]
    table = Table(data, colWidths=col_widths)
    styles = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True)
    ])
    table.setStyle(styles)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def get_account_currency(transaction: Transaction) -> str:
    if transaction.sender_account:
        return transaction.sender_account.get_account_currency_display()
    return transaction.receiver_account.get_account_currency_display()
