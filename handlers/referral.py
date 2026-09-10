from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database import models
from config import BOT_USERNAME, REFERRAL_JOIN_BONUS, REFERRAL_ACTIVE_BONUS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    referred_by = None
    if args:
        try:
            ref_id = int(args[0])
            if ref_id != user.id:
                referred_by = ref_id
        except ValueError:
            pass

    existing = models.get_or_create_user(user.id, user.username or user.first_name, referred_by)

    if referred_by and existing["referred_by"] == referred_by:
        models.add_coins(referred_by, REFERRAL_JOIN_BONUS)

    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    balance = models.get_balance(user.id)

    await update.message.reply_text(
        "🎲 *Ludo Turnir Botiga xush kelibsiz!*\n\n"
        f"💰 Balansingiz: {balance} coin\n\n"
        "Buyruqlar:\n"
        "/shop — do'kon (kub, token, tema)\n"
        "/profil — hisobingiz\n"
        "/taklif — do'st taklif qilish linki\n"
        "/turnir — turnirga yozilish\n"
        "/reyting — top o'yinchilar\n\n"
        f"🔗 Sizning taklif linkingiz:\n`{link}`\n"
        f"Har bir do'stingiz shu link orqali qo'shilsa +{REFERRAL_JOIN_BONUS} coin, "
        f"u faol o'ynay boshlasa yana +{REFERRAL_ACTIVE_BONUS} coin olasiz!",
        parse_mode="Markdown",
    )


async def referral_link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    models.get_or_create_user(user.id, user.username or user.first_name)
    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    count = models.get_referral_count(user.id)
    await update.message.reply_text(
        f"🔗 *Sizning taklif linkingiz:*\n`{link}`\n\n"
        f"👥 Taklif qilganlaringiz: {count} ta\n\n"
        f"Do'stlaringizga shu linkni yuboring — ular bot orqali qo'shilsa, "
        f"sizga coin va maxsus skinlar ochiladi!",
        parse_mode="Markdown",
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = models.get_or_create_user(user.id, user.username or user.first_name)
    count = models.get_referral_count(user.id)
    await update.message.reply_text(
        f"👤 *Profil*\n\n"
        f"Ism: {user.first_name}\n"
        f"💰 Coin: {u['coins']}\n"
        f"👥 Taklif qilganlar: {count}\n"
        f"🎲 Kub: {u['dice_skin']}\n"
        f"🚩 Token: {u['token_skin']}\n"
        f"🗺 Tema: {u['board_theme']}",
        parse_mode="Markdown",
    )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = models.get_leaderboard(10)
    if not top:
        await update.message.reply_text("Hozircha reytingda hech kim yo'q.")
        return
    text = "🏆 *Top O'yinchilar*\n\n"
    for i, row in enumerate(top, 1):
        name = row["username"] or "Foydalanuvchi"
        text += f"{i}. {name} — {row['coins']} coin\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def mark_active_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    became_active = models.mark_active(user.id)
    if became_active:
        referrer = models.get_referrer(user.id)
        if referrer:
            models.add_coins(referrer, REFERRAL_ACTIVE_BONUS)
            try:
                await context.bot.send_message(
                    referrer,
                    f"🎉 Taklif qilgan do'stingiz faollashdi! +{REFERRAL_ACTIVE_BONUS} coin oldingiz.",
                )
            except Exception:
                pass
        await update.message.reply_text("✅ Faollik qayd etildi, rahmat!")
    else:
        await update.message.reply_text("Siz allaqachon faol sifatida qayd etilgansiz.")


def register(app):
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("taklif", referral_link_command))
    app.add_handler(CommandHandler("profil", profile_command))
    app.add_handler(CommandHandler("reyting", leaderboard_command))
    app.add_handler(CommandHandler("oynadim", mark_active_command))
