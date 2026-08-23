from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI(title="1xBet Pattern Tracker")

def get_db():
    conn = sqlite3.connect("1xbet_tracker.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def read_dashboard(category: str = None):
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Récupération des catégories et compteurs
    cursor.execute("SELECT * FROM category_stats")
    stats = [dict(row) for row in cursor.fetchall()]
    
    # 2. Récupération avec formatage de la date (JJ/MM) et de l'heure (HH:MM:SS)
    query = """
        SELECT id, league, home_team, away_team, odds_type, category,
               strftime('%d/%m %H:%M:%S', captured_at) as capture_datetime
        FROM matches
    """
    if category and category != "all":
        query += " WHERE category = ? ORDER BY captured_at DESC LIMIT 20"
        cursor.execute(query, (category,))
    else:
        query += " ORDER BY captured_at DESC LIMIT 20"
        cursor.execute(query)
        category = "all"
        
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # 3. Construction de l'interface HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="30">
        <title>1xBet Pattern Tracker</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }}
            .card {{ background-color: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 20px; color: #38bdf8; margin-top: 0; }}
            h2 {{ font-size: 16px; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px; margin-top: 0; }}
            
            .categories-container {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 12px; }}
            .cat-btn {{ background-color: #334155; color: #f8fafc; padding: 8px 14px; border-radius: 20px; text-decoration: none; font-size: 13px; font-weight: bold; white-space: nowrap; }}
            .cat-btn.active {{ background-color: #0284c7; color: white; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
            th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #334155; font-size: 13px; }}
            th {{ color: #94a3b8; font-weight: 600; }}
            .datetime-tag {{ color: #38bdf8; font-weight: bold; font-size: 11px; background-color: #0f172a; padding: 4px 6px; border-radius: 4px; border: 1px solid #0284c7; white-space: nowrap; }}
            .badge {{ background-color: #0284c7; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
            .btn {{ display: block; width: 100%; text-align: center; background-color: #0284c7; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: bold; text-decoration: none; margin-top: 12px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>1xBet Pattern Tracker</h1>
            <a href="/" class="btn">🔄 Actualiser / Réinitialiser</a>
        </div>

        <div class="card">
            <h2>Filtre par Catégorie</h2>
            <div class="categories-container">
                <a href="/?category=all" class="cat-btn {'active' if category == 'all' else ''}">Toutes les catégories</a>
    """
    
    for s in stats:
        cat_name = s.get('category', 'N/A')
        count = s.get('total_matches', 0)
        is_active = 'active' if category == cat_name else ''
        html_content += f'<a href="/?category={cat_name}" class="cat-btn {is_active}">{cat_name} ({count})</a>'

    html_content += f"""
            </div>
        </div>

        <div class="card">
            <h2>Matchs Capturés — <span style="color:#38bdf8;">{"Toutes" if category == "all" else category}</span></h2>
            <table>
                <thead>
                    <tr>
                        <th>Horodatage</th>
                        <th>Match</th>
                        <th>Détails</th>
                    </tr>
                </thead>
                <tbody>
    """

    if not matches:
        html_content += '<tr><td colspan="3" style="text-align:center; color:#64748b;">Aucun match capturé.</td></tr>'
    else:
        for m in matches:
            datetime_str = m.get('capture_datetime') or '--/-- --:--'
            html_content += f"""
            <tr>
                <td><span class="datetime-tag">📅 {datetime_str}</span></td>
                <td>
                    <b>{m.get('home_team')} vs {m.get('away_team')}</b><br>
                    <small style='color:#64748b'>{m.get('league')}</small>
                </td>
                <td><span class='badge'>{m.get('odds_type')}</span></td>
            </tr>
            """

    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html_content
