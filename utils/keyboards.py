# utils/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def seller_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Seller main menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton("➕ Add Product", callback_data="add_product")],
        [InlineKeyboardButton("📦 My Products", callback_data="my_products")],
        [InlineKeyboardButton("📬 Orders Received", callback_data="orders_received")],
    ]
    return InlineKeyboardMarkup(keyboard)


def buyer_menu_keyboard() -> InlineKeyboardMarkup:
    """
    (Optional for future) Buyer main menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
        [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")],
        [InlineKeyboardButton("✅ Checkout", callback_data="checkout")],
        [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
    ]
    return InlineKeyboardMarkup(keyboard)
