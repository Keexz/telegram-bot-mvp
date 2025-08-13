# services/seller_service.py
import time
from typing import Tuple
from db import (
    is_seller_registered as db_is_seller_registered,
    save_otp,
    validate_otp,
    mark_otp_used,
    get_db_connection,
)

# In-memory OTP attempts tracking: {telegram_id: {"count": int, "last_try": timestamp}}
otp_attempts = {}

# Max attempts allowed per registration session
MAX_OTP_ATTEMPTS = 3


def is_seller_registered(telegram_id: int) -> bool:
    """
    Check if seller already exists in the DB.
    """
    return db_is_seller_registered(telegram_id)


def reset_otp_attempts(telegram_id: int) -> None:
    """
    Reset OTP attempt tracking for a new registration flow.
    """
    otp_attempts[telegram_id] = {"count": 0, "last_try": time.time()}


def check_otp_and_mark(telegram_id: int, otp_code: str):
    """
    Check if OTP is valid and unused, with attempt limit.
    If valid, mark it as used in DB.
    Returns:
        (True, None) on success
        (False, remaining_attempts) on wrong OTP
        (False, "error_message") if other validation issue
    """
    # Initialize attempts if needed
    if telegram_id not in otp_attempts:
        reset_otp_attempts(telegram_id)

    # Block if attempts exceeded
    if otp_attempts[telegram_id]["count"] >= MAX_OTP_ATTEMPTS:
        return False, 0

    # Count this attempt
    otp_attempts[telegram_id]["count"] += 1
    otp_attempts[telegram_id]["last_try"] = time.time()

    # Validate OTP in DB
    is_valid, message = validate_otp(otp_code)
    if not is_valid:
        remaining = MAX_OTP_ATTEMPTS - otp_attempts[telegram_id]["count"]
        return False, remaining

    # OTP valid → mark as used
    mark_otp_used(otp_code)
    return True, None


def register_seller_full(telegram_id, name, username, business_name, email, phone):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if seller already exists
    cursor.execute("SELECT id FROM sellers WHERE telegram_id = %s", (telegram_id,))
    if cursor.fetchone():
        conn.close()
        return False  # Already exists

    query = """
        INSERT INTO sellers (telegram_id, name, username, business_name, email, phone)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (telegram_id, name, username, business_name, email, phone))
    conn.commit()

    cursor.close()
    conn.close()
    return True



def cancel_session(telegram_id: int) -> None:
    """
    Cancel registration session and clear OTP tracking for the user.
    """
    if telegram_id in otp_attempts:
        del otp_attempts[telegram_id]
