import sqlite3
from contextlib import contextmanager
from config import DB_PATH, START_BALANCE


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                coins INTEGER DEFAULT 0,
                referred_by INTEGER,
                is_active INTEGER DEFAULT 0,
                dice_skin TEXT DEFAULT 'Default',
                token_skin TEXT DEFAULT 'Default',
                board_theme TEXT DEFAULT 'Default',
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS owned_skins (
                user_id INTEGER,
                skin_type TEXT,
                skin_name TEXT,
                PRIMARY KEY (user_id, skin_type, skin_name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                status TEXT DEFAULT 'open',
                winner_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tournament_players (
                tournament_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (tournament_id, user_id)
            )
        """)


def get_or_create_user(user_id: int, username: str, referred_by: int = None):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row:
            return row
        conn.execute(
            "INSERT INTO users (user_id, username, coins, referred_by) VALUES (?, ?, ?, ?)",
            (user_id, username, START_BALANCE, referred_by),
        )
        conn.execute(
            "INSERT OR IGNORE INTO owned_skins (user_id, skin_type, skin_name) VALUES (?, 'dice', 'Default')",
            (user_id,),
        )
        conn.execute(
            "INSERT OR IGNORE INTO owned_skins (user_id, skin_type, skin_name) VALUES (?, 'token', 'Default')",
            (user_id,),
        )
        conn.execute(
            "INSERT OR IGNORE INTO owned_skins (user_id, skin_type, skin_name) VALUES (?, 'board', 'Default')",
            (user_id,),
        )
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def add_coins(user_id: int, amount: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))


def get_balance(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT coins FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["coins"] if row else 0


def mark_active(user_id: int) -> bool:
    """Foydalanuvchini aktiv deb belgilaydi. True qaytarsa - birinchi marta aktiv bo'ldi."""
    with get_conn() as conn:
        row = conn.execute("SELECT is_active FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row and row["is_active"] == 0:
            conn.execute("UPDATE users SET is_active=1 WHERE user_id=?", (user_id,))
            return True
        return False


def get_referrer(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["referred_by"] if row else None


def owns_skin(user_id: int, skin_type: str, skin_name: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM owned_skins WHERE user_id=? AND skin_type=? AND skin_name=?",
            (user_id, skin_type, skin_name),
        ).fetchone()
        return row is not None


def buy_skin(user_id: int, skin_type: str, skin_name: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO owned_skins (user_id, skin_type, skin_name) VALUES (?, ?, ?)",
            (user_id, skin_type, skin_name),
        )


def equip_skin(user_id: int, skin_type: str, skin_name: str):
    column = {"dice": "dice_skin", "token": "token_skin", "board": "board_theme"}[skin_type]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {column}=? WHERE user_id=?", (skin_name, user_id))


def get_referral_count(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE referred_by=?", (user_id,)
        ).fetchone()
        return row["c"]


def get_leaderboard(limit: int = 10):
    with get_conn() as conn:
        return conn.execute(
            "SELECT username, coins FROM users ORDER BY coins DESC LIMIT ?", (limit,)
        ).fetchall()

