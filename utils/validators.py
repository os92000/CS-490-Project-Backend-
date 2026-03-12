import re
from email_validator import validate_email, EmailNotValidError

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
