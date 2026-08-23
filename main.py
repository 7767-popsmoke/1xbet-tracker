from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI(title="1xBet Pattern Tracker")

def get_db():
    conn = sqlite3.connect("1xbet_tracker.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def read_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupération des statistiques
    cursor.execute("SELECT * FROM category_stats")
    stats = [dict(row) for row in cursor.fetchall()]
    
    # Récupération des 10 derniers matchs capturés
    cursor.execute("SELECT * FROM matches ORDER BY captured_at DESC LIMIT 10")
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Génération du tableau de bord HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>1xBet Pattern Tracker</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }}
            .card {{ background-color: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 20px; color: #38bdf8; margin-top: 0; }}
            h2 {{ font-size: 16px; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
            .status {{ display: flex; align-items: center; gap: 8px; font-weight: bold; color: #4ade80; }}
            .dot {{ height: 10px; width: 10px; background-color: #4ade80; border-radius: 50%; display: inline-block; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
            th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #334155; font-size: 14px; }}
            th {{ color: #94a3b8; font-weight: 600; }}
            .badge {{ background-color: #0284c7; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
            .btn {{ display: block; width: 100%; text-align: center; background-color: #0284c7; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: bold; text-decoration: none; margin-top: 12px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>1xBet Pattern Tracker</h1>
            <div class="status"><span class="dot"></span> Serveur Opérationnel</div>
            <a href="/" class="btn">🔄 Actualiser les données</a>
        </div>

        <div class="card">
            <h2>Statistiques par Catégorie</h2>
            <table>
                <thead>
                    <tr><th>Catégorie</th><th>Matchs Capturés</th></tr>
                </thead>
                <tbody>
    """
    
    if not stats:
        html_content += '<tr><td colspan="2" style="text-align:center; color:#64748b;">Aucune donnée accumulée pour le moment</td></tr>'
    else:
        for s in stats:
            html_content += f"<tr><td><span class='badge'>{s.get('category', 'N/A')}</span></td><td><b>{s.get('total_matches', 0)}</b></td></tr>"

    html_content += """
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>Dernières Captures (T-30s)</h2>
            <table>
                <thead>
                    <tr><th>Match</th><th>Cote / Catégorie</th></tr>
                </thead>
                <tbody>
    """

    if not matches:
        html_content += '<tr><td colspan="2" style="text-align:center; color:#64748b;">En attente des prochains matchs...</td></tr>'
    else:
        for m in matches:
            html_content += f"<tr><td>{m.get('home_team')} vs {m.get('away_team')}<br><small style='color:#64748b'>{m.get('league')}</small></td><td>{m.get('odds_type')}</td></tr>"

    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html_content
