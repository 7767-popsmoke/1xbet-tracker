import time
import sqlite3
import requests

TELEGRAM_BOT_TOKEN = "8924253079:AAFfGzy32vZbpIVFVt1yuvPQnKrTTix0H6U"
TELEGRAM_CHAT_ID = "2123037767"

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
        f"⏱️ *Temps:* 00:00 (Coup d'envoi)\n"
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

def save_match(match_id, league, home, away, odds_info, category_name, ht_score, yellow_cards, red_cards):
    conn = sqlite3.connect("1xbet_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM matches WHERE id = ?", (str(match_id),))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            INSERT INTO matches (id, league, home_team, away_team, odds_type, category, ht_score, yellow_cards, red_cards)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(match_id), league, home, away, odds_info, category_name, ht_score, yellow_cards, red_cards))
        
        cursor.execute("""
            INSERT INTO category_stats (category, total_matches)
            VALUES (?, 1)
            ON CONFLICT(category) DO UPDATE SET total_matches = total_matches + 1
        """, (category_name,))
        
        conn.commit()
        conn.close()

        send_telegram_alert(home, away, league, odds_info, category_name)
        print(f"[CAPTURE & ALERT] {category_name} -> {home} vs {away}")
    else:
        conn.close()

def get_decimal_part(odds_val):
    return round((odds_val - int(odds_val)) * 100)

def compute_decimal_combination(c1, cx, c2):
    d1 = get_decimal_part(c1)
    dx = get_decimal_part(cx)
    d2 = get_decimal_part(c2)

    if dx > d1 and dx > d2:
        if d1 < d2:
            return "[1 < X > 2]"
        elif d2 < d1:
            return "[2 < X > 1]"
        else:
            return "[1 = 2 < X]"

    items = [("1", d1), ("X", dx), ("2", d2)]
    items_sorted = sorted(items, key=lambda item: item[1])

    val0, val1, val2 = items_sorted[0][1], items_sorted[1][1], items_sorted[2][1]
    lbl0, lbl1, lbl2 = items_sorted[0][0], items_sorted[1][0], items_sorted[2][0]

    op1 = "=" if val0 == val1 else "<"
    op2 = "=" if val1 == val2 else "<"

    return f"[{lbl0} {op1} {lbl1} {op2} {lbl2}]"

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
                time_sec = sc_data.get("TS", -1)
                
                # Extraction du score mi-temps et cartons si disponibles
                periods = sc_data.get("PS", [])
                ht_score = "0-0"
                if len(periods) > 0:
                    p1 = periods[0].get("Value", {})
                    ht_score = f"{p1.get('S1', 0)}-{p1.get('S2', 0)}"

                # Extraction des cartons
                card_data = sc_data.get("S", [])
                yellow_cards = "0-0"
                red_cards = "0-0"
                for stat in card_data:
                    if stat.get("Key") == "YellowCards":
                        yellow_cards = f"{stat.get('Value', {}).get('S1', 0)}-{stat.get('Value', {}).get('S2', 0)}"
                    elif stat.get("Key") == "RedCards":
                        red_cards = f"{stat.get('Value', {}).get('S1', 0)}-{stat.get('Value', {}).get('S2', 0)}"

                if time_sec == 0:
                    events = m.get("E", [])
                    cote_1 = None
                    cote_x = None
                    cote_2 = None
                    
                    for e in events:
                        if e.get("T") == 1:
                            cote_1 = e.get("C")
                        elif e.get("T") == 2:
                            cote_x = e.get("C")
                        elif e.get("T") == 3:
                            cote_2 = e.get("C")

                    if cote_1 and cote_x and cote_2:
                        int_1 = int(cote_1)
                        int_x = int(cote_x)
                        int_2 = int(cote_2)

                        base_pattern = None
                        if int_1 == 2 and int_x == 3 and int_2 == 3:
                            base_pattern = "2/3/3"
                        elif int_1 == 3 and int_x == 3 and int_2 == 2:
                            base_pattern = "3/3/2"

                        if base_pattern:
                            decimal_comb = compute_decimal_combination(cote_1, cote_x, cote_2)
                            category_name = f"{base_pattern} {decimal_comb}"
                            details_cotes = f"1: {cote_1} | X: {cote_x} | 2: {cote_2}"
                            
                            save_match(match_id, league, home_team, away_team, details_cotes, category_name, ht_score, yellow_cards, red_cards)
                
    except Exception as e:
        print(f"[ERREUR] Échec de la récupération 1xBet : {e}")

def start_scraper():
    init_db()
    print("Scraper 1xBet (Cotes 2/3/3 & 3/3/2 avec Mi-temps & Cartons) démarré...")
    while True:
        fetch_1xbet_live()
        time.sleep(15)

if __name__ == "__main__":
    start_scraper()
