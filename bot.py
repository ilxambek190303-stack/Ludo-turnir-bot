import asyncio
import json
import logging
import os
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "tournaments.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# ---------------- persistence ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tournaments, f, ensure_ascii=False, indent=2)


tournaments = load_data()  # key: str(chat_id) -> tournament dict


def get_t(chat_id):
    return tournaments.get(str(chat_id))


def new_tournament(admin_id):
    return {
        "status": "registration",  # registration | in_progress | finished
        "players": {},  # user_id(str) -> name
        "matches": [],  # list of {id, p1, p2, p1_name, p2_name, winner}
        "admin_id": admin_id,
    }


# ---------------- helpers ----------------
def round_robin_pairs(player_ids):
    ids = player_ids[:]
    if len(ids) % 2 == 1:
        ids.append(None)  # bye
    n = len(ids)
    pairs = []
    for _ in range(n - 1):
        for i in range(n // 2):
            a, b = ids[i], ids[n - 1 - i]
            if a is not None and b is not None:
                pairs.append((a, b))
        ids.insert(1, ids.pop())
    return pairs


def standings_text(t):
    stats = {uid: {"w": 0, "l": 0, "played": 0} for uid in t["players"]}
    for m in t["matches"]:
        if m["winner"]:
            loser = m["p1"] if m["winner"] == m["p2"] else m["p2"]
            stats[m["winner"]]["w"] += 1
            stats[m["winner"]]["played"] += 1
            stats[loser]["l"] += 1
            stats[loser]["played"] += 1

    rows = []
    for uid, s in stats.items():
        rows.append((t["players"][uid], s["w"], s["l"], s["played"]))
    rows.sort(key=lambda r: (-r[1], r[2]))

    lines = ["🏆 <b>Turnir jadvali</b>\n"]
    for i, (name, w, l, played) in enumerate(rows, 1):
        lines.append(f"{i}. {name} — {w}G {l}M ({played} o'yin)")
    return "\n".join(lines)


def match_keyboard(match):
    kb = InlineKeyboardBuilder()
    kb.button(text=f"🏆 {match['p1_name']}", callback_data=f"win:{match['id']}:{match['p1']}")
    kb.button(text=f"🏆 {match['p2_name']}", callback_data=f"win:{match['id']}:{match['p2']}")
    kb.adjust(2)
    return kb.as_markup()


# ---------------- handlers ----------------
@dp.message(Command("turnir"))
async def cmd_help(message: Message):
    await message.answer(
        "🎲 <b>Ludo turnir bot</b>\n\n"
        "/royxat — yangi turnir uchun ro'yxatni ochish (admin)\n"
        "/boshla — ro'yxatni yopib, jadval tuzish (admin)\n"
        "/holat — joriy jadvalni ko'rish\n"
        "/yakunla — turnirni yakunlash (admin)",
        parse_mode="HTML",
    )


@dp.message(Command("royxat"))
async def cmd_register(message: Message):
    if message.chat.type == "private":
        await message.answer("Bu buyruq faqat guruhlarda ishlaydi.")
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ("administrator", "creator"):
        await message.answer("Faqat guruh admini turnir ochishi mumkin.")
        return

    t = new_tournament(message.from_user.id)
    tournaments[str(message.chat.id)] = t
    save_data()

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Qatnashaman", callback_data="join")
    await message.answer(
        "🏆 <b>Yangi Ludo turniri!</b>\n\n"
        "Ishtirok etish uchun pastdagi tugmani bosing.\n"
        "Admin /boshla buyrug'ini yuborganda ro'yxat yopiladi.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "join")
async def cb_join(cb: CallbackQuery):
    t = get_t(cb.message.chat.id)
    if not t or t["status"] != "registration":
        await cb.answer("Ro'yxat hozircha ochiq emas.", show_alert=True)
        return

    uid = str(cb.from_user.id)
    if uid in t["players"]:
        await cb.answer("Siz allaqachon ro'yxatdasiz.")
        return

    t["players"][uid] = cb.from_user.full_name
    save_data()

    names = "\n".join(f"• {n}" for n in t["players"].values())
    await cb.message.edit_text(
        f"🏆 <b>Yangi Ludo turniri!</b>\n\nIshtirokchilar ({len(t['players'])}):\n{names}\n\n"
        "Admin /boshla buyrug'ini yuborganda ro'yxat yopiladi.",
        reply_markup=cb.message.reply_markup,
        parse_mode="HTML",
    )
    await cb.answer("Ro'yxatga qo'shildingiz!")


@dp.message(Command("boshla"))
async def cmd_start_tournament(message: Message):
    t = get_t(message.chat.id)
    if not t or t["status"] != "registration":
        await message.answer("Faol ro'yxat topilmadi. Avval /royxat yuboring.")
        return
    if message.from_user.id != t["admin_id"]:
        await message.answer("Faqat turnirni ochgan admin boshlashi mumkin.")
        return
    if len(t["players"]) < 3:
        await message.answer("Kamida 3 ta ishtirokchi kerak.")
        return

    player_ids = list(t["players"].keys())
    random.shuffle(player_ids)
    pairs = round_robin_pairs(player_ids)

    matches = []
    for i, (a, b) in enumerate(pairs, 1):
        matches.append(
            {
                "id": i,
                "p1": a,
                "p2": b,
                "p1_name": t["players"][a],
                "p2_name": t["players"][b],
                "winner": None,
            }
        )
    t["matches"] = matches
    t["status"] = "in_progress"
    save_data()

    await message.answer(
        f"📋 Jadval tuzildi — jami {len(matches)} ta o'yin.\n"
        "Har bir juftlik o'zaro kelishib (mini-app orqali) o'ynaydi, so'ng g'olibni "
        "pastdagi tugma orqali belgilaydi."
    )
    for m in matches:
        await message.answer(
            f"{m['id']}) {m['p1_name']} 🆚 {m['p2_name']}",
            reply_markup=match_keyboard(m),
        )


@dp.callback_query(F.data.startswith("win:"))
async def cb_report_win(cb: CallbackQuery):
    _, match_id, winner_id = cb.data.split(":")
    match_id = int(match_id)

    t = get_t(cb.message.chat.id)
    if not t or t["status"] != "in_progress":
        await cb.answer("Turnir faol emas.", show_alert=True)
        return

    match = next((m for m in t["matches"] if m["id"] == match_id), None)
    if not match:
        await cb.answer("O'yin topilmadi.", show_alert=True)
        return

    uid = str(cb.from_user.id)
    if uid not in (match["p1"], match["p2"]) and cb.from_user.id != t["admin_id"]:
        await cb.answer(
            "Faqat shu o'yin qatnashchilari yoki admin natijani belgilashi mumkin.",
            show_alert=True,
        )
        return

    match["winner"] = winner_id
    save_data()

    winner_name = match["p1_name"] if winner_id == match["p1"] else match["p2_name"]
    await cb.message.edit_text(
        f"{match['id']}) {match['p1_name']} 🆚 {match['p2_name']}\n✅ G'olib: {winner_name}"
    )
    await cb.answer("Natija saqlandi!")


@dp.message(Command("holat"))
async def cmd_status(message: Message):
    t = get_t(message.chat.id)
    if not t:
        await message.answer("Bu guruhda hali turnir yo'q.")
        return
    await message.answer(standings_text(t), parse_mode="HTML")


@dp.message(Command("yakunla"))
async def cmd_finish(message: Message):
    t = get_t(message.chat.id)
    if not t:
        await message.answer("Bu guruhda hali turnir yo'q.")
        return
    if message.from_user.id != t["admin_id"]:
        await message.answer("Faqat admin turnirni yakunlashi mumkin.")
        return

    unfinished = [m for m in t["matches"] if not m["winner"]]
    text = standings_text(t)
    if unfinished:
        text += f"\n\n⚠️ {len(unfinished)} ta o'yin natijasi hali belgilanmagan."

    t["status"] = "finished"
    save_data()
    await message.answer("🏁 <b>Turnir yakunlandi!</b>\n\n" + text, parse_mode="HTML")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
