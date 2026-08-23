from fastapi import FastAPI
import sqlite3

app = FastAPI(title="1xBet Pattern Tracker")

def get_db():
    conn = sqlite3.connect("1xbet_tracker.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"status": "online", "message": "API 1xBet Tracker opérationnelle"}

@app.get("/leagues/list")
def get_leagues():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT league FROM matches")
    leagues = [row["league"] for row in cursor.fetchall()]
    conn.close()
    return {"leagues": leagues}

@app.get("/stats/categories")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM category_stats")
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"data": stats}
