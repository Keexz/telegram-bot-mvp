import re

def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    Returns True if email looks valid, False otherwise.
    """
    if not email or "@" not in email:
        return False
    #Basic regex for validating an email
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number with optional '+' and 7-15 digits.
    E.g., +2348012345678 or 08012345678.
    """
    if not phone:
        return False
    # Allow optional +, country code, and numbers (7 to 15 digits)
    pattern =  r"^\+?\d{7,15}$"
    return re.match(pattern, phone) is not None