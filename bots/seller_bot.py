import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from services.seller_service import (
    is_seller_registered,
    reset_otp_attempts,
    check_otp_and_mark,
    register_seller_full,
    cancel_session
)

from utils.validators import is_valid_email, is_valid_phone
from utils.keyboards import seller_menu_keyboard

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

# Conversation states
OTP_STEP, BUSINESS_NAME, EMAIL, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    If the user is already a registered seller, show the seller menu.
    Otherwise, begin OTP flow.
    """
    user = update.effective_user
    user_id = user.id
    try:
        if is_seller_registered(user_id):
            await update.message.reply_text(f"👋 Welcome back, {user.first_name or user.full_name}!")
            await update.message.reply_text("Seller Menu:", reply_markup=seller_menu_keyboard())
            return ConversationHandler.END
    except Exception as exc:
        logger.exception("Error checking seller registration for %s: %s", user_id, exec)
        await update.message.reply_text("⚠️ Could not check your account right now. Please try again later.")
        return ConversationHandler.END
    
    # Not registered -> reset attempts and ask for OTP
    reset_otp_attempts(user_id)
    await update.message.reply_text(
        "🔐 Please enter your seller registration OTP:\n\n"
        "⚠️ The OTP is valid for 24 hours and can only be used once."
    )
    return OTP_STEP

async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Validate OTP with attempt limit handled by the service layer.
    Return next state on success or repeats OTP step with remaining attempts.
    """
    user = update.effective_chat
    user_id = user.id
    otp_code = (update.message.text or "").strip()
    try:
        ok, remaining_or_msg = check_otp_and_mark(user_id, otp_code)
    except Exception as exc:
        logger.exception("Error validating OTP for %s: %s", user_id, exc)
        await update.message.reply_text("⚠️ An internal error occurred while validating your OTP. Try again later.")
        return ConversationHandler.END
    
    if not ok:
        #Remaining_or_msg is remaining attempts (int) or error string
        if isinstance(remaining_or_msg, int):
            remaining = remaining_or_msg
            if remaining <= 0:
                await update.message.reply_text(
                    "🚫 You've reached the maximum number of OTP attempts. Please contact admin for a new code."
                )
                return ConversationHandler.END
            await update.message.reply_text(
                f"❌ Invalid or expired OTP. You have {remaining} attempts remaining. Try again:"
            )
            return OTP_STEP
        else:
            await update.message.reply_text(str(remaining_or_msg))
            return OTP_STEP
            
    # OTP OK -> move to business name
    await update.message.reply_text(
        "✅ OTP verified!\n\nLet's register your business.\n"
        "Please send your *Business Name* (e.g., FreshFarm Foods).",
        parse_mode="Markdown",
    )
    return BUSINESS_NAME

async def handle_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    business_name = (update.message.text or "").strip()
    if len(business_name) < 2:
        await update.message.reply_text("❗ Business name is too short. Please enter a valid name.")
        return BUSINESS_NAME
    
    context.user_data["business_name"] = business_name
    await update.message.reply_text("📧 Great! Now send your *business email* (e.g., shop@example.com).", parse_mode="Markdown")
    return EMAIL

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = (update.message.text or "").strip()
    if not is_valid_email(email):
        await update.message.reply_text("❗ That doesn't look like a valid email. Try again (e.g., shop@example.com).")
        return EMAIL
    
    context.user_data["email"] = email
    await update.message.reply_text(
        "📱 Got it. Finally, send your *phone number* with country code (e.g., +2348012345678).",
        parse_mode="Markdown",
    )
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = (update.message.text or "").strip()
    if not is_valid_phone(phone):
        await update.message.reply_text("❗ Invalid phone format. Include country code (e.g., +2348012345678).")
        return PHONE
    
    user = update.effective_user
    user_id = user.id
    business_name = context.user_data.get("business_name")
    email = context.user_data.get("email")

    try:
        success = register_seller_full(
            telegram_id=user_id,
            name=user.full_name,
            username=user.username or "",
            business_name=business_name,
            email=email,
            phone=phone,
        )
    except Exception as exc:
        logger.exception("Error registering seller %s: %s", user_id, exc)
        await update.message.reply_text("⚠️ Failed to create your seller account. Please try again later.")
        return ConversationHandler.END
    
    if not success:
        await update.message.reply_text(
            "⚠️ You already have a seller account registered with this Telegram account.",
            reply_markup=seller_menu_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text("🎉 Your seller account has been created successfully!")
    await update.message.reply_text("Seller Menu:", reply_markup=seller_menu_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    #Clear ephemeral session state
    cancel_session(user_id)
    context.user_data.clear()
    await update.message.reply_text("❌ Registration cancelled. You can start again anytime with /start.")
    return ConversationHandler.END

#Optional: future callback query handler for seller menu actions (placeholders)
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # You can route based on data here. For now, placeholders:
    if data == "add_product":
        await query.edit_message_text("Coming soon")
    elif data == "my_products":
        await query.edit_message_text("Coming soon")
    elif data == "orders_received":
        await query.edit_message_text("Coming soon")
    else:
        await query.edit_message_text("Unknown action. Use /start to open the menu.")
        
def register_handlers(application):
    """
     Attach conversation + menu handlers to your telegram.ext.Application.

    Example:
        from telegram.ext import ApplicationBuilder
        from bots.seller_bot import register_handlers

        app = ApplicationBuilder().token(BOT_TOKEN).build()
        register_handlers(app)
        app.run_polling()
    """
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            OTP_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp)],
            BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_business_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=False,
    )
    
    application.add_handler(conv)
    application.add_handler(CallbackQueryHandler(menu_callback))