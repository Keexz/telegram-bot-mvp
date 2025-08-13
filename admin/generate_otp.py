# generate_otp.py
import random
import string
from datetime import datetime, timedelta
from db import save_otp

def generate_otp(length=6) -> str:
    """Generate a numeric OTP of given length."""
    return ''.join(random.choices(string.digits, k=length))

def main():
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(hours=24)
    save_otp(otp_code, expires_at)
    print(f"✅ OTP generated: {otp_code}")
    print("⚠️ This OTP will expire in 24 hours and can only be used once.")

if __name__ == "__main__":
    main()
