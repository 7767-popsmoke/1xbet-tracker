import time
import sqlite3
import requests

# ⚠️ VOS INFORMATIONS TELEGRAM
TELEGRAM_BOT_TOKEN = "VOTRE_TOKEN_BOT_ICI"
TELEGRAM_CHAT_ID = "VOTRE_CHAT_ID_ICI"

ONEXBET_LIVE_URL = "https://1xbet.com/LiveFeed/Get1x2_VZip?sports=1&count=100&lng=fr"

def send_telegram_alert(home_team, away_team, league, odds_info, category):
    if TELEGRAM_BOT_TOKEN == "VOTRE_TOKEN_BOT_ICI":
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"🚨 *PROFIL DE COTE DÉTECTÉ ({category})*\n\n"
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

def save_match(match_id, league, home, away, odds_info, category_name):
    conn = sqlite3.connect("1xbet_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM matches WHERE id = ?", (str(match_id),))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            INSERT INTO matches (id, league, home_team, away_team, odds_type, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(match_id), league, home, away, odds_info, category_name))
        
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
                
                # 1. VÉRIFICATION DU TEMPS EXACT DE DÉBUT (00:00 / 0 seconde)
                time_sec = m.get("SC", {}).get("TS", -1)
                
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

                        detected_category = None

                        # Condition 1 : Cotes Domicile=2.xx, Nul=3.xx, Extérieur=3.xx
                        if int_1 == 2 and int_x == 3 and int_2 == 3:
                            detected_category = "Pattern 2/3/3"

                        # Condition 2 : Cotes Domicile=3.xx, Nul=3.xx, Extérieur=2.xx
                        elif int_1 == 3 and int_x == 3 and int_2 == 2:
                            detected_category = "Pattern 3/3/2"

                        # 2. ENREGISTREMENT ET ALERTE SI LE MOTIF EST DETECTÉ
                        if detected_category:
                            details_cotes = f"1: {cote_1} | X: {cote_x} | 2: {cote_2}"
                            save_match(match_id, league, home_team, away_team, details_cotes, detected_category)
                
    except Exception as e:
        print(f"[ERREUR] Échec de la récupération 1xBet : {e}")

def start_scraper():
    init_db()
    print("Scraper 1xBet Live (Filtres 2/3/3 et 3/3/2 à 00:00) démarré...")
    while True:
        fetch_1xbet_live()
        # Scan réactif toutes les 15 secondes pour intercepter le 00:00 pile
        time.sleep(15)

if __name__ == "__main__":
    start_scraper()
