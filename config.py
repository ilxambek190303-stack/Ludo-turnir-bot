import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8939000345:AAEi2mp61SLhd-w3SmlC0ketdqlHHZ8ZxMQ")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@Ludov2_bot") # @ belgisisiz

# Coin sozlamalari
REFERRAL_JOIN_BONUS = 50      # do'st guruhga qo'shilganda taklif qilganga beriladi
REFERRAL_ACTIVE_BONUS = 30    # taklif qilingan odam birinchi o'yin o'ynasa qo'shimcha
START_BALANCE = 200           # yangi userga boshlang'ich coin

# Turnir sozlamalari
TOURNAMENT_MIN_PLAYERS = 4
TOURNAMENT_WIN_COIN = 500

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "bot.db")
