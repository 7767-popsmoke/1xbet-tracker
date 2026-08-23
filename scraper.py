import time
import sqlite3
import requests

TELEGRAM_BOT_TOKEN = "VOTRE_TOKEN_BOT_ICI"
TELEGRAM_CHAT_ID = "VOTRE_CHAT_ID_ICI"

ONEXBET_LIVE_URL = "https://1xbet.com/LiveFeed/Get1x2_VZip?sports=1&count=100&lng=fr"

def send_telegram_alert(home_team, away_team, league, odds_info, category):
    if TELEGRAM_BOT_TOKEN == "VOTRE_TOKEN_BOT_ICI":
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"🚨 *NOUVEAU PATTERN DÉTECTÉ*\n"
        f"🏷️ *Catégorie:* `{category}`\n\n"
        f"🏆 *Ligue:* {league}\n"
        f"⚔️ *Match:* {home_team} vs {away_team}\n"
        f"⏱️ *Temps:* Avant coup d'envoi / 00:00\n"
        f"📊 *Cotes:* {odds_info}\n\n"
        f"📲 _Consultez votre tableau de bord_"
    )
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")

def init_db():
    conn = sqlite3.connect("1xbet_tracker.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            odds_type TEXT,
            category TEXT,
            ht_score TEXT DEFAULT '0-0',
            yellow_cards TEXT DEFAULT '0-0',
            red_cards TEXT DEFAULT '0-0',
            status TEXT DEFAULT 'pending',
            is_eligible INTEGER DEFAULT 1,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_stats (
            category TEXT PRIMARY KEY,
            total_matches INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def parse_category(o1: float, ox: float, o2: float):
    def get_tier(val):
        if 2.00 <= val <= 2.99:
            return 2
        elif 3.00 <= val <= 3.99:
            return 3
        return None

    t1, tx, t2 = get_tier(o1), get_tier(ox), get_tier(o2)

    if None in (t1, tx, t2):
        return None

    base_pattern = f"{t1}/{tx}/{t2}"
    if base_pattern not in ["2/3/3", "3/3/2"]:
        return None

    if o1 < ox and ox < o2:
        variant = "[1 < X < 2]"
    elif o1 < o2 and o2 < ox:
        variant = "[1 < 2 < X]"
    elif ox < o1 and o1 < o2:
        variant = "[X < 1 < 2]"
    elif ox < o2 and o2 < o1:
        variant = "[X < 2 < 1]"
    elif o2 < o1 and o1 < ox:
        variant = "[2 < 1 < X]"
    elif o2 < ox and ox < o1:
        variant = "[2 < X < 1]"
    elif o1 == ox and ox < o2:
        variant = "[1 = X < 2]"
    elif o2 < o1 and o1 == ox:
        variant = "[2 < 1 = X]"
    elif o1 == o2 and o2 < ox:
        variant = "[1 = 2 < X]"
    elif ox < o1 and o1 == o2:
        variant = "[X < 1 = 2]"
    elif ox == o2 and o2 < o1:
        variant = "[X = 2 < 1]"
    elif o1 < ox and ox == o2:
        variant = "[1 < X = 2]"
    elif o1 == ox and ox == o2:
        variant = "[1 = X = 2]"
    elif o1 < ox and ox > o2:
        variant = "[1 < X > 2]"
    elif o2 < ox and ox > o1:
        variant = "[2 < X > 1]"
    else:
        variant = "[1 < X < 2]"

    return f"{base_pattern} {variant}"

def save_or_update_match(match_id, league, home, away, odds_info, category_name, ht_score, yellow_cards, red_cards):
    conn = sqlite3.connect("1xbet_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, category FROM matches WHERE id = ?", (str(match_id),))
    existing = cursor.fetchone()

    if not existing:
        if category_name:
            cursor.execute("""
                INSERT INTO matches (id, league, home_team, away_team, odds_type, category, ht_score, yellow_cards, red_cards, status, is_eligible)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 1)
            """, (str(match_id), league, home, away, odds_info, category_name, ht_score, yellow_cards, red_cards))
            
            cursor.execute("""
                INSERT INTO category_stats (category, total_matches)
                VALUES (?, 1)
                ON CONFLICT(category) DO UPDATE SET total_matches = total_matches + 1
            """, (category_name,))
            
            conn.commit()
            send_telegram_alert(home, away, league, odds_info, category_name)
            print(f"[NOUVEAU MATCH] {category_name} -> {home} vs {away}")
    else:
        if category_name:
            cursor.execute("""
                UPDATE matches 
                SET odds_type = ?, category = ?, ht_score = ?, yellow_cards = ?, red_cards = ?, is_eligible = 1
                WHERE id = ?
            """, (odds_info, category_name, ht_score, yellow_cards, red_cards, str(match_id)))
        else:
            cursor.execute("""
                UPDATE matches SET is_eligible = 0 WHERE id = ? AND status = 'pending'
            """, (str(match_id),))
        conn.commit()

    conn.close()

def fetch_1xbet_live():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(ONEXBET_LIVE_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = data.get("Value", [])
            
            for m in matches:
                match_id = m.get("I")
                league = m.get("L", "Ligue Inconnue")
                home_team = m.get("O1", "Équipe 1")
                away_team = m.get("O2", "Équipe 2")
                
                sc_data = m.get("SC", {})
                time_sec = sc_data.get("TS", 0)
                
                # Extraction score mi-temps
                periods = sc_data.get("PS", [])
                ht_score = "0-0"
                if len(periods) > 0:
                    p1 = periods[0].get("Value", {})
                    ht_score = f"{p1.get('S1', 0)}-{p1.get('S2', 0)}"

                # Extraction cartons
                card_data = sc_data.get("S", [])
                yellow_cards = "0-0"
                red_cards = "0-0"
                for stat in card_data:
                    if stat.get("Key") == "YellowCards":
                        yellow_cards = f"{stat.get('Value', {}).get('S1', 0)}-{stat.get('Value', {}).get('S2', 0)}"
                    elif stat.get("Key") == "RedCards":
                        red_cards = f"{stat.get('Value', {}).get('S1', 0)}-{stat.get('Value', {}).get('S2', 0)}"

                # Extraction des cotes
                events = m.get("E", [])
                cote_1, cote_x, cote_2 = None, None, None
                
                for e in events:
                    if e.get("T") == 1:
                        cote_1 = e.get("C")
                    elif e.get("T") == 2:
                        cote_x = e.get("C")
                    elif e.get("T") == 3:
                        cote_2 = e.get("C")

                if cote_1 and cote_x and cote_2:
                    category_name = parse_category(float(cote_1), float(cote_x), float(cote_2))
                    details_cotes = f"1: {cote_1} | X: {cote_x} | 2: {cote_2}"
                    
                    save_or_update_match(match_id, league, home_team, away_team, details_cotes, category_name, ht_score, yellow_cards, red_cards)
                
    except Exception as e:
        print(f"[ERREUR SCRAPER] {e}")

def start_scraper():
    init_db()
    print("Scraper 1xBet Live Tracker opérationnel...")
    while True:
        fetch_1xbet_live()
        time.sleep(15)

if __name__ == "__main__":
    start_scraper()
