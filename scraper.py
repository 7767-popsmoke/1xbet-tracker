import time
import sqlite3
import requests

# Endpoints publics utilisés par 1xBet pour le direct
ONEXBET_LIVE_URL = "https://1xbet.com/LiveFeed/Get1x2_VZip?sports=1&count=50&lng=fr"

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

def save_match(match_id, league, home, away, odds_info):
    conn = sqlite3.connect("1xbet_tracker.db")
    cursor = conn.cursor()
    
    # Insertion du match capturé
    cursor.execute("""
        INSERT OR IGNORE INTO matches (id, league, home_team, away_team, odds_type, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (str(match_id), league, home, away, odds_info, "Football Live"))
    
    # Mise à jour du compteur de la catégorie
    cursor.execute("""
        INSERT INTO category_stats (category, total_matches)
        VALUES ('Football Live', 1)
        ON CONFLICT(category) DO UPDATE SET total_matches = total_matches + 1
    """, ())
    
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
                
                # Vérification du temps de jeu (ex: fin de match / T-30s)
                time_sec = m.get("SC", {}).get("TS", 0)
                
                # Extraction des cotes principales (1X2)
                events = m.get("E", [])
                odds_desc = f"{len(events)} cotes disponibles"
                
                save_match(match_id, league, home_team, away_team, odds_desc)
                print(f"[CAPTURE] Match enregistré : {home_team} vs {away_team} ({league})")
                
    except Exception as e:
        print(f"[ERREUR] Échec de la récupération des flux : {e}")

def start_scraper():
    init_db()
    print("Scraper 1xBet Live démarré...")
    while True:
        fetch_1xbet_live()
        # Scan toutes les 60 secondes pour éviter d'être bloqué par 1xBet
        time.sleep(60)

if __name__ == "__main__":
    start_scraper()
