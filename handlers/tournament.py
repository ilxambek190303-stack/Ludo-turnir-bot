from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database import models
from database.models import get_conn
from config import TOURNAMENT_MIN_PLAYERS, TOURNAMENT_WIN_COIN


async def tournament_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Turnir faqat guruh ichida ochiladi. Botni guruhga qo'shing.")
        return

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM tournaments WHERE group_id=? AND status='open'", (chat.id,)
        ).fetchone()
        if row:
            tid = row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO tournaments (group_id, status) VALUES (?, 'open')", (chat.id,)
            )
            tid = cur.lastrowid

    count = _player_count(tid)
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Qatnashaman", callback_data=f"joint:{tid}")],
            [InlineKeyboardButton("🏁 Turnirni boshlash", callback_data=f"startt:{tid}")],
        ]
    )
    await update.message.reply_text(
        f"🏆 *Turnir ochildi!* (ID: {tid})\n\n"
        f"Qatnashish uchun tugmani bosing.\n"
        f"Hozirgi qatnashchilar: {count}\n"
        f"Kamida {TOURNAMENT_MIN_PLAYERS} kishi kerak.\n"
        f"G'olib uchun mukofot: {TOURNAMENT_WIN_COIN} coin + maxsus skin!",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


def _player_count(tid: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM tournament_players WHERE tournament_id=?", (tid,)
        ).fetchone()
        return row["c"]


async def join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tid = int(query.data.split(":")[1])
    user = query.from_user
    models.get_or_create_user(user.id, user.username or user.first_name)

    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tournament_players (tournament_id, user_id) VALUES (?, ?)",
            (tid, user.id),
        )

    count = _player_count(tid)
    await query.answer(f"Siz turnirga qo'shildingiz! Hozirgi qatnashchilar: {count}", show_alert=True)


async def start_tournament_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tid = int(query.data.split(":")[1])
    count = _player_count(tid)

    if count < TOURNAMENT_MIN_PLAYERS:
        await query.answer(
            f"Kamida {TOURNAMENT_MIN_PLAYERS} kishi kerak. Hozircha: {count}", show_alert=True
        )
        return

    with get_conn() as conn:
        players = conn.execute(
            "SELECT user_id FROM tournament_players WHERE tournament_id=?", (tid,)
        ).fetchall()
        conn.execute("UPDATE tournaments SET status='ongoing' WHERE id=?", (tid,))

    await query.answer("Turnir boshlandi!")
    await query.edit_message_text(
        f"🏁 *Turnir boshlandi!*\n\n"
        f"Qatnashchilar soni: {count}\n\n"
        f"Endi Ludo King ilovasida o'zaro o'ynang va g'olibni "
        f"`/golib <user_id>` buyrug'i bilan admin e'lon qiladi.",
        parse_mode="Markdown",
    )


async def declare_winner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not context.args:
        await update.message.reply_text("Foydalanish: /golib <user_id>")
        return

    try:
        winner_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id raqam bo'lishi kerak.")
        return

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM tournaments WHERE group_id=? AND status='ongoing' ORDER BY id DESC LIMIT 1",
            (chat.id,),
        ).fetchone()
        if not row:
            await update.message.reply_text("Faol turnir topilmadi.")
            return
        tid = row["id"]
        conn.execute(
            "UPDATE tournaments SET status='finished', winner_id=? WHERE id=?", (winner_id, tid)
        )

    models.add_coins(winner_id, TOURNAMENT_WIN_COIN)
    await update.message.reply_text(
        f"🏆 Tabriklaymiz! G'olib: {winner_id}\n+{TOURNAMENT_WIN_COIN} coin berildi!"
    )


def register(app):
    app.add_handler(CommandHandler("turnir", tournament_command))
    app.add_handler(CommandHandler("golib", declare_winner_command))
    app.add_handler(CallbackQueryHandler(join_callback, pattern="^joint:"))
    app.add_handler(CallbackQueryHandler(start_tournament_callback, pattern="^startt:"))
