from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database import models
from database.shop_data import CATALOG, TYPE_LABELS
from database.models import get_referral_count


def _type_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"shoptype:{key}")]
        for key, label in TYPE_LABELS.items()
    ]
    return InlineKeyboardMarkup(buttons)


def _skin_list_keyboard(user_id: int, skin_type: str):
    items = CATALOG[skin_type]
    buttons = []
    for name, info in items.items():
        owned = models.owns_skin(user_id, skin_type, name)
        if owned:
            label = f"✅ {name}"
        elif info["referrals"] > 0:
            label = f"🔒 {name} — {info['price']} coin / {info['referrals']} taklif"
        else:
            label = f"🔒 {name} — {info['price']} coin"
        buttons.append([InlineKeyboardButton(label, callback_data=f"buy:{skin_type}:{name}")])
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="shopmenu")])
    return InlineKeyboardMarkup(buttons)


async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    models.get_or_create_user(user.id, user.username or user.first_name)
    balance = models.get_balance(user.id)
    await update.message.reply_text(
        f"🛍 *Do'kon*\nBalansingiz: {balance} coin\n\nQaysi bo'limni ko'rmoqchisiz?",
        reply_markup=_type_menu_keyboard(),
        parse_mode="Markdown",
    )


async def shop_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🛍 *Do'kon*\n\nQaysi bo'limni ko'rmoqchisiz?",
        reply_markup=_type_menu_keyboard(),
        parse_mode="Markdown",
    )


async def shop_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    skin_type = query.data.split(":")[1]
    user_id = query.from_user.id
    label = TYPE_LABELS[skin_type]
    await query.edit_message_text(
        f"{label}\n\n✅ = sizda bor / 🔒 = sotib olish kerak",
        reply_markup=_skin_list_keyboard(user_id, skin_type),
    )


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, skin_type, skin_name = query.data.split(":")
    user_id = query.from_user.id
    user = models.get_or_create_user(user_id, query.from_user.username or query.from_user.first_name)

    if models.owns_skin(user_id, skin_type, skin_name):
        models.equip_skin(user_id, skin_type, skin_name)
        await query.answer(f"{skin_name} tanlandi! ✅", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=_skin_list_keyboard(user_id, skin_type))
        return

    info = CATALOG[skin_type][skin_name]
    balance = models.get_balance(user_id)
    referrals = get_referral_count(user_id)

    if info["referrals"] > 0 and referrals < info["referrals"]:
        await query.answer(
            f"Bu skin uchun kamida {info['referrals']} ta do'st taklif qilishingiz kerak.\n"
            f"Hozircha: {referrals} ta.",
            show_alert=True,
        )
        return

    if balance < info["price"]:
        await query.answer(
            f"Coin yetarli emas! Kerak: {info['price']}, sizda: {balance}",
            show_alert=True,
        )
        return

    models.add_coins(user_id, -info["price"])
    models.buy_skin(user_id, skin_type, skin_name)
    models.equip_skin(user_id, skin_type, skin_name)
    await query.answer(f"🎉 {skin_name} sotib olindi va tanlandi!", show_alert=True)
    await query.edit_message_reply_markup(reply_markup=_skin_list_keyboard(user_id, skin_type))


def register(app):
    app.add_handler(CommandHandler("shop", shop_command))
    app.add_handler(CallbackQueryHandler(shop_menu_callback, pattern="^shopmenu$"))
    app.add_handler(CallbackQueryHandler(shop_type_callback, pattern="^shoptype:"))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy:"))
