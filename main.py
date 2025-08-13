# main.py
import os
from telegram.ext import ApplicationBuilder
from bots import seller_bot
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ SELLER_BOT_TOKEN not found in environment variables.")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register seller bot handlers
    seller_bot.register_handlers(application)

    print("🚀 Seller bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
