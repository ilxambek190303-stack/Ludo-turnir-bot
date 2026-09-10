# Rasmlardagi (Ludo King Inventory) skinlar asosida tuzilgan katalog
# narx = coin, referrals = shu skinni ochish uchun kerak bo'lgan taklif soni (ixtiyoriy, 0 = faqat coin bilan)

DICE_SKINS = {
    "Default":       {"price": 0,    "referrals": 0},
    "Super King":     {"price": 300,  "referrals": 0},
    "Halloween":      {"price": 800,  "referrals": 2},
    "Football":       {"price": 800,  "referrals": 2},
    "New Year":       {"price": 800,  "referrals": 2},
    "Tri-Colour":     {"price": 800,  "referrals": 2},
    "Heart":          {"price": 800,  "referrals": 2},
    "Colors":         {"price": 800,  "referrals": 2},
    "Summer":         {"price": 800,  "referrals": 2},
    "Monsoon Boat":   {"price": 650,  "referrals": 1},
    "Sixer":          {"price": 800,  "referrals": 2},
    "Cricket King":   {"price": 800,  "referrals": 2},
    "Diya":           {"price": 800,  "referrals": 2},
    "Pumpkin":        {"price": 800,  "referrals": 2},
    "Republic":       {"price": 800,  "referrals": 2},
    "Dragon":         {"price": 1500, "referrals": 5},
}

TOKEN_SKINS = {
    "Default":    {"price": 0,    "referrals": 0},
    "Hammer":     {"price": 1000, "referrals": 3},
    "Ninja":      {"price": 1000, "referrals": 3},
    "Super Hero": {"price": 1000, "referrals": 3},
}

BOARD_THEMES = {
    "Default":   {"price": 0,    "referrals": 0},
    "Egypt":     {"price": 1200, "referrals": 3},
    "Nature":    {"price": 900,  "referrals": 2},
    "Disco":     {"price": 900,  "referrals": 2},
    "Marble":    {"price": 900,  "referrals": 2},
    "Candy":     {"price": 900,  "referrals": 2},
    "Christmas": {"price": 900,  "referrals": 2},
    "Penguin":   {"price": 900,  "referrals": 2},
    "Battle":    {"price": 900,  "referrals": 2},
    "Diwali":    {"price": 900,  "referrals": 2},
}

CATALOG = {
    "dice": DICE_SKINS,
    "token": TOKEN_SKINS,
    "board": BOARD_THEMES,
}

TYPE_LABELS = {
    "dice": "🎲 Kublar",
    "token": "🚩 Figuralar (Token)",
    "board": "🗺 Taxta temalari",
}
