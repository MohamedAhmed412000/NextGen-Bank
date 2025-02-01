import hashlib
import hmac
import random
import string
from os import getenv

BANK_CARD_PREFIX = getenv('BANK_CARD_PREFIX')
BANK_CARD_CODE = getenv('BANK_CARD_CODE')

def generate_card_number(prefix=BANK_CARD_PREFIX, card_code=BANK_CARD_CODE, length=16) -> str:
    total_prefix = prefix + card_code
    random_digits_length = length - len(total_prefix) - 1

    if random_digits_length < 0:
        raise ValueError('Prefix and code are too long for card_number generation')

    random_digits = ''.join(random.choices(string.digits, k=random_digits_length))
    card_number = total_prefix + random_digits

    digits = [int(d) for d in random_digits]
    for i in range(len(digits)-1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    
    check_digit = (10 - sum(digits) % 10) % 10
    return card_number + str(check_digit)

def generate_card_cvv(card_number: str, expiry_date: str) -> str:
    secret_key = getenv('CVV_SECRET_KEY').encode('utf8')
    data = f'{card_number}-{expiry_date}'.encode('utf8')
    hmac_obj = hmac.new(secret_key, data, hashlib.sha256)
    cvv = str(int(hmac_obj.hexdigest(), 16))[:3]
    return cvv.zfill(3)
