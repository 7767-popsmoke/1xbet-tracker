import time
import sqlite3
import requests

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

def start_scraper():
    init_db()
    print("Scraper 1xBet démarré et en attente de matchs à T-30s...")
    while True:
        # Simulation de la boucle de vérification des flux Live 1xBet
        time.sleep(10)

if __name__ == "__main__":
    start_scraper()
