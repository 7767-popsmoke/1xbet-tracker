import time
import sqlite3
import requests

# ⚠️ REMPLACEZ PAR VOS INFORMATIONS TELEGRAM
TELEGRAM_BOT_TOKEN = "8924253079:AAFfGzy32vZbpIVFVt1yuvPQnKrTTix0H6U"
TELEGRAM_CHAT_ID = "2123037767"

ONEXBET_LIVE_URL = "https://1xbet.com/LiveFeed/Get1x2_VZip?sports=1&count=50&lng=fr"

# 1. FONCTION DE NOTIFICATION TELEGRAM
def send_telegram_alert(home_team, away_team, league, odds_info):
    if TELEGRAM_BOT_TOKEN == "VOTRE_TOKEN_BOT_ICI":
        return  # Ne fait rien si le token n'est pas rempli

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"🚨 *NOUVEAU MATCH CAPTURÉ (T-30s)*\n\n"
        f"🏆 *Ligue:* {league}\n"
        f"⚔️ *Match:* {home_team} vs {away_team}\n"
        f"📊 *Détails:* {odds_info}\n\n"
        f"📲 _Regardez votre tableau de bord_"
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

# 2. INITIALISATION DE LA BASE DE DONNÉES
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

# 3. ENREGISTREMENT EN BASE ET DÉCLENCHEMENT DE L'ALERTE
def save_match(match_id, league, home, away, odds_info):
    conn = sqlite3.connect("1xbet_tracker.db")
    cursor = conn.cursor()
    
    # Vérification anti-doublon
    cursor.execute("SELECT id FROM matches WHERE id = ?", (str(match_id),))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            INSERT INTO matches (id, league, home_team, away_team, odds_type, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(match_id), league, home, away, odds_info, "Football Live"))
        
        cursor.execute("""
            INSERT INTO category_stats (category, total_matches)
            VALUES ('Football Live', 1)
            ON CONFLICT(category) DO UPDATE SET total_matches = total_matches + 1
        """, ())
        
        conn.commit()
        conn.close()

        # Envoi de la notification
        send_telegram_alert(home, away, league, odds_info)
        print(f"[CAPTURE & ALERT] Notification envoyée pour {home} vs {away}")
    else:
        conn.close()

# 4. RÉCUPÉRATION DES FLUX EN DIRECT
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
                events = m.get("E", [])
                odds_desc = f"{len(events)} cotes disponibles"
                
                save_match(match_id, league, home_team, away_team, odds_desc)
                
    except Exception as e:
        print(f"[ERREUR] Échec de la récupération des flux : {e}")

# 5. BOUCLE PRINCIPALE
def start_scraper():
    init_db()
    print("Scraper 1xBet Live démarré...")
    while True:
        fetch_1xbet_live()
        time.sleep(60)

if __name__ == "__main__":
    start_scraper()
