import random
import db

def generate_otp():
    """Generate a random 6-digit OTP code"""
    return str(random.randint(100000, 999999))

if __name__ == "__main__":
    otp_code = generate_otp()
    db.save_otp(otp_code)
    print(f"✅ New OTP generated: {otp_code}")
    print("📌 This OTP will expire in 24 hours and can only be used once.")