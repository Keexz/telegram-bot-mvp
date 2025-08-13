import os
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def is_buyer_registered(telegram_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT * FROM buyers WHERE telegram_id = %s"
    cursor.execute(query, (telegram_id,))  # FIX: added comma for single tuple
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result is not None

def register_buyer(telegram_id, name, username):
    db = get_db_connection()
    cursor = db.cursor()
    query = "INSERT INTO buyers (telegram_id, name, username) VALUES (%s, %s, %s)"
    cursor.execute(query, (telegram_id, name, username))
    db.commit()
    cursor.close()
    db.close()

def is_seller_registered(telegram_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT * FROM sellers WHERE telegram_id = %s"
    cursor.execute(query, (telegram_id,))  # FIX: added comma for single tuple
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result is not None

def register_seller(telegram_id, name, username, business_name, email, phone):
    db = get_db_connection()
    cursor = db.cursor()
    query = "INSERT INTO sellers (telegram_id, name, username, business_name, email, phone) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (telegram_id, name, username, business_name, email, phone))
    db.commit()
    cursor.close()
    db.close()

# SELLER OTP FUNCTIONS

def save_otp(otp_code, expires_at):
    """save a new OTP with a 24-hours expiration"""
    db = get_db_connection()
    cursor = db.cursor()
    expires_at = datetime.now() + timedelta(hours=24)
    query = "INSERT INTO seller_otps (otp_code, expires_at, used) VALUES (%s, %s, %s)"
    cursor.execute(query, (otp_code, expires_at, False))
    db.commit()
    cursor.close()
    db.close()
    
def validate_otp(otp_code):
    """Check if OTP is valid, unused, and not expired"""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT * FROM seller_otps
        WHERE otp_code = %s
        AND used = FALSE
        AND expires_at > NOW()
    """
    cursor.execute(query, (otp_code,))
    otp = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not otp:
        return False, "OTP not found."
    
    if otp["used"]:
        return False, "OTP already used."
    
    if  otp["expires_at"] < datetime.now():
        return False, "OTP expired."
    
    return True, "OTP is valid"

def mark_otp_used(otp_code):
    """Mark an OTP as used so it can't be reused"""
    db = get_db_connection()
    cursor = db.cursor()
    query = "UPDATE seller_otps SET used = TRUE WHERE otp_code = %s"
    cursor.execute(query, (otp_code,))
    db.commit()
    cursor.close()
    db.close()