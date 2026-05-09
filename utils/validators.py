import re
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import re

def is_valid_email(email):
    """Validate email format"""
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def is_valid_password(password):
    """
    Validate password strength
    Requirements: At least 8 characters, 1 uppercase, 1 lowercase, 1 digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, "Password is valid"

def is_valid_role(role):
    """Validate user role"""
    valid_roles = ['client', 'coach', 'both', 'admin']
    return role in valid_roles

def is_valid_fitness_level(level):
    """Validate fitness level"""
    valid_levels = ['beginner', 'intermediate', 'advanced']
    return level in valid_levels

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data
    Returns: (is_valid, missing_fields)
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    return len(missing_fields) == 0, missing_fields


def _luhn_check(card_number: str) -> bool:
    """Perform Luhn algorithm to validate a card number (basic sanity check)."""
    try:
        digits = [int(d) for d in re.sub(r"\D", "", card_number)]
    except Exception:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _get_card_brand(card_number: str) -> str:
    """Return a simple card brand guess based on IIN ranges."""
    num = re.sub(r"\D", "", card_number)
    if num.startswith('4'):
        return 'visa'
    if num[:2] in ('51', '52', '53', '54', '55') or 2221 <= int(num[:4]) <= 2720:
        return 'mastercard'
    if num.startswith('34') or num.startswith('37'):
        return 'amex'
    if num.startswith('6'):
        return 'discover'
    return 'unknown'


def validate_card_info(card: dict):
    """Validate minimal card information without storing sensitive data.

    Expects card dict with: number, exp_month, exp_year, cvc
    Returns (True, meta) or (False, error_message)
    meta includes: last4, brand, exp_month, exp_year
    """
    if not isinstance(card, dict):
        return False, 'Card information must be an object'

    required = ['number', 'exp_month', 'exp_year', 'cvc']
    ok, missing = validate_required_fields(card, required)
    if not ok:
        return False, f'Missing card fields: {", ".join(missing)}'

    number = re.sub(r"\s+", "", str(card.get('number', '')))
    try:
        exp_month = int(card.get('exp_month'))
        exp_year = int(card.get('exp_year'))
    except Exception:
        return False, 'Invalid expiry month/year'

    cvc = str(card.get('cvc'))

    if not _luhn_check(number):
        return False, 'Card number failed Luhn check'

    if not (1 <= exp_month <= 12):
        return False, 'Invalid expiry month'

    # Normalize two-digit years to 4-digit
    if exp_year < 100:
        exp_year += 2000

    now = datetime.utcnow()
    # Card is valid through the end of the expiry month
    if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
        return False, 'Card has expired'

    if not re.fullmatch(r"\d{3,4}", cvc):
        return False, 'Invalid CVC format'

    brand = _get_card_brand(number)
    last4 = number[-4:]

    meta = {
        'last4': last4,
        'brand': brand,
        'exp_month': exp_month,
        'exp_year': exp_year,
    }
    return True, meta
