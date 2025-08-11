from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from dotenv import load_dotenv
import os
import db

load_dotenv()

# Conversation states
OTP_STEP, BUSINESS_NAME, EMAIL, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # check if this Telegram user is already registered as a seller
    if db.is_seller_registered(user_id):
        await update.message.reply_text(
            f"👋 Welcome back {update.effective_user.first_name}!"
        )
        await show_seller_menu(update)
        return ConversationHandler.END # End onboarding
    
    # If not registered, start OTP process
    await update.message.reply_text(
        "🔐 Please enter your seller registration OTP:\n\n"
        "⚠️ The OTP is valid for 24 hours and can only be used once."
    )
    return OTP_STEP

# Step 1: Validate OTP
async def check_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    
    if db.validate_otp(otp_code):
        db.mark_otp_used(otp_code) # Mark OTP so it cn't be reused
        await update.message.reply_text(
            "✅ OTP verified!\n\n"
            "Let's get your business registered.\n"
            "Please enter your **Business Name** 🏪\n\n"
            "_Example:_ FreshFarm Foods",
            parse_mode="Markdown"
        )
        return BUSINESS_NAME
    else:
        await update.message.reply_text(
            "❌ Invalid or expired OTP. Please contact the admin for a new code."
        )
        return ConversationHandler.END
    
# Step 2: Collect Business Name
async def collect_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["business_name"] = update.message.text
    await update.message.reply_text(
        "✅ Got it!\n\n"
        "Now, please enter your **Business Email** 📧\n\n"
        "_Example:_ `myshop@example.com`",
        parse_mode="Markdown"
    )
    return EMAIL

#Step 3: Collect Email
async def collect_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text(
        "Perfect 👍\n\n"
        "Lastly, please enter your **Phone Number** 📱\n\n"
        "_Example:_ `+2348012345678`",
        parse_mode="Markdown"
    )
    return PHONE

#Step 4: Collect Phone and Save
async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    
    user = update.effective_user
    db.register_seller(
        telegram_id=user.id,
        name=user.full_name,
        username=user.username or "",
        business_name=context.user_data["business_name"],
        email=context.user_data["email"],
        phone=context.user_data["phone"]
    )
    
    await update.message.reply_text("🎉 Your seller account has been created successfully!")
    await show_seller_menu(update)
    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Registration cancelled.")
    return ConversationHandler.END

# Seller Menu
async def show_seller_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("Register", callback_data="vendor_register")],
        [InlineKeyboardButton("Add Product", callback_data="add_product")],
        [InlineKeyboardButton("My Products", callback_data="my_products")],
        [InlineKeyboardButton("Orders Received", callback_data="orders_received")]
    ]
    if update.message:
        await update.message.reply_text("Seller Menu:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text("Seller Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

# Menu Button Actions
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    if choice == "vendor_register":
        await query.edit_message_text("📝 You are already registered as a seller.")
    elif choice == "add_product":
        await query.edit_message_text("➕ Add product (coming soon)")
    elif choice == "my_products":
        await query.edit_message_text("📦 My products (coming soon)")
    elif choice == "orders_recieved":
        await query.edit_message_text("📬 Orders received (coming soon)")

# Main
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            OTP_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_otp)],
            BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_business_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_phone)],
        },
        fallbacks=[CommandHandler("Cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(menu_callback))
    
    print("Seller bot is running...")
    app.run_polling()