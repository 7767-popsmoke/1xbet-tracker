from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI(title="1xBet Pattern Tracker")

# Génération exhaustive des 26 catégories théoriques
VARIANTS = [
    "[1 < X < 2]", "[1 < 2 < X]", "[X < 1 < 2]", "[X < 2 < 1]",
    "[2 < 1 < X]", "[2 < X < 1]", "[1 = X < 2]", "[2 < 1 = X]",
    "[1 = 2 < X]", "[X < 1 = 2]", "[X = 2 < 1]", "[1 < X = 2]",
    "[1 = X = 2]", "[1 < X > 2]", "[2 < X > 1]"
]

ALL_THEORETICAL_CATEGORIES = []
for base in ["2/3/3", "3/3/2"]:
    for v in VARIANTS:
        ALL_THEORETICAL_CATEGORIES.append(f"{base} {v}")

def get_db():
    conn = sqlite3.connect("1xbet_tracker.db")
    conn.row_factory = sqlite3.Row
    return conn

def check_and_update_schema(conn):
    """ Ajoute automatiquement les nouvelles colonnes si elles manquent """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(matches)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "is_eligible" not in columns:
        cursor.execute("ALTER TABLE matches ADD COLUMN is_eligible INTEGER DEFAULT 1")
    if "status" not in columns:
        cursor.execute("ALTER TABLE matches ADD COLUMN status TEXT DEFAULT 'confirmed'")
    conn.commit()

@app.get("/", response_class=HTMLResponse)
def read_dashboard(category: str = None, league: str = None):
    try:
        conn = get_db()
        check_and_update_schema(conn)
        cursor = conn.cursor()

        # Compteurs
        cursor.execute("SELECT category, COUNT(*) as total_matches FROM matches WHERE is_eligible = 1 GROUP BY category")
        db_cat_counts = {row["category"]: row["total_matches"] for row in cursor.fetchall()}

        cursor.execute("SELECT league, COUNT(*) as total_matches FROM matches WHERE is_eligible = 1 GROUP BY league ORDER BY league ASC")
        leagues_stats = [dict(row) for row in cursor.fetchall()]

        # Construction de la requête SQL
        query = """
            SELECT id, league, home_team, away_team, odds_type, category,
                   COALESCE(ht_score, '0-0') as ht_score,
                   COALESCE(yellow_cards, '0-0') as yellow_cards,
                   COALESCE(red_cards, '0-0') as red_cards,
                   COALESCE(status, 'confirmed') as match_status,
                   strftime('%d/%m %H:%M:%S', captured_at) as capture_datetime
            FROM matches
            WHERE is_eligible = 1
        """
        params = []

        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        else:
            category = "all"

        if league and league != "all":
            query += " AND league = ?"
            params.append(league)
        else:
            league = "all"

        query += " ORDER BY captured_at DESC LIMIT 50"

        cursor.execute(query, params)
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()

    except Exception as e:
        return HTMLResponse(content=f"<h2>Une erreur SQLite est survenue : {str(e)}</h2><p>Vérifiez que la table 'matches' existe bien dans 1xbet_tracker.db.</p>", status_code=500)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="15">
        <title>1xBet Live Tracker</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }}
            .card {{ background-color: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 20px; color: #38bdf8; margin: 0 0 12px 0; }}
            h2 {{ font-size: 15px; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px; margin-top: 0; }}

            .tabs-header {{ display: flex; gap: 8px; margin-bottom: 12px; border-bottom: 2px solid #334155; padding-bottom: 8px; }}
            .tab-btn {{ background: none; border: none; color: #94a3b8; font-weight: bold; font-size: 14px; padding: 8px 12px; cursor: pointer; border-radius: 6px; }}
            .tab-btn.active {{ background-color: #0284c7; color: white; }}

            .volet-container {{ display: none; }}
            .volet-container.active {{ display: block; }}

            .select-dropdown {{
                width: 100%;
                background-color: #0f172a;
                color: #38bdf8;
                border: 1px solid #0284c7;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 6px;
                outline: none;
            }}

            .table-responsive {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
            th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #334155; font-size: 12px; }}
            th {{ color: #94a3b8; font-weight: 600; white-space: nowrap; }}
            
            .datetime-tag {{ color: #38bdf8; font-weight: bold; font-size: 11px; background-color: #0f172a; padding: 4px 6px; border-radius: 4px; border: 1px solid #0284c7; white-space: nowrap; }}
            .badge {{ background-color: #0284c7; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
            .stats-tag {{ background-color: #334155; padding: 3px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: nowrap; }}
            
            .status-pending {{ background-color: #eab308; color: #0f172a; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; }}
            .status-confirmed {{ background-color: #22c55e; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; }}

            .reset-btn {{ display: inline-block; background-color: #0284c7; color: white; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: bold; text-decoration: none; margin-bottom: 12px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📊 1xBet Live Tracker & Analytics</h1>
            <a href="/" class="reset-btn">🔄 Réinitialiser tous les filtres</a>
        </div>

        <div class="card">
            <div class="tabs-header">
                <button class="tab-btn active" onclick="switchTab('categories')">🏷️ Fenêtre des Catégories</button>
                <button class="tab-btn" onclick="switchTab('leagues')">🏆 Fenêtre des Championnats</button>
            </div>

            <!-- VOLET 1 : CATÉGORIES -->
            <div id="volet-categories" class="volet-container active">
                <label style="font-size: 12px; color: #94a3b8; font-weight: bold;">Catégories de cotes requises (2/3/3 et 3/3/2) :</label>
                <select class="select-dropdown" onchange="filterByCategory(this.value)">
                    <option value="all" {'selected' if category == 'all' else ''}>
                        -- Toutes les catégories ({sum(db_cat_counts.values())} matchs valides) --
                    </option>
    """

    for cat in ALL_THEORETICAL_CATEGORIES:
        match_count = db_cat_counts.get(cat, 0)
        selected = 'selected' if category == cat else ''
        html_content += f'<option value="{cat}" {selected}>{cat} — ({match_count} matchs)</option>'

    html_content += f"""
                </select>
            </div>

            <!-- VOLET 2 : CHAMPIONNATS -->
            <div id="volet-leagues" class="volet-container">
                <label style="font-size: 12px; color: #94a3b8; font-weight: bold;">Championnats capturés :</label>
                <select class="select-dropdown" onchange="filterByLeague(this.value)">
                    <option value="all" {'selected' if league == 'all' else ''}>
                        -- Tous les championnats ({sum(l['total_matches'] for l in leagues_stats)} matchs) --
                    </option>
    """

    for l in leagues_stats:
        lg_name = l['league']
        count = l['total_matches']
        selected = 'selected' if league == lg_name else ''
        html_content += f'<option value="{lg_name}" {selected}>{lg_name} — ({count} matchs)</option>'

    html_content += f"""
                </select>
            </div>
        </div>

        <!-- TABLEAU DE RÉSULTATS -->
        <div class="card">
            <h2>Matchs Suivis — <span style="color:#38bdf8;">Catégorie: {"Toutes" if category == "all" else category} | Ligue: {"Toutes" if league == "all" else league}</span></h2>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Horodatage</th>
                            <th>Suivi Cote</th>
                            <th>Championnat</th>
                            <th>Match</th>
                            <th>Score MT</th>
                            <th>Cartons</th>
                            <th>Catégorie Final</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    if not matches:
        html_content += '<tr><td colspan="7" style="text-align:center; color:#64748b; padding: 20px;">Aucun match trouvé.</td></tr>'
    else:
        for m in matches:
            datetime_str = m.get('capture_datetime') or '--/-- --:--'
            st = m.get('match_status')
            status_badge = '<span class="status-pending">⏳ En suivi (Pre-match)</span>' if st == 'pending' else '<span class="status-confirmed">✅ Validé à 00:00</span>'

            html_content += f"""
            <tr>
                <td><span class="datetime-tag">📅 {datetime_str}</span></td>
                <td>{status_badge}</td>
                <td><small style='color:#94a3b8'>{m.get('league')}</small></td>
                <td><b>{m.get('home_team')} vs {m.get('away_team')}</b></td>
                <td><span class="stats-tag">⚽ {m.get('ht_score')}</span></td>
                <td>
                    <span class="stats-tag">🟨 {m.get('yellow_cards')}</span>
                    <span class="stats-tag" style="color: #ef4444;">🟥 {m.get('red_cards')}</span>
                </td>
                <td><span class='badge'>{m.get('category')}</span></td>
            </tr>
            """

    html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            function switchTab(tabName) {{
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.volet-container').forEach(cont => cont.classList.remove('active'));

                if (tabName === 'categories') {{
                    document.querySelectorAll('.tab-btn')[0].classList.add('active');
                    document.getElementById('volet-categories').classList.add('active');
                }} else {{
                    document.querySelectorAll('.tab-btn')[1].classList.add('active');
                    document.getElementById('volet-leagues').classList.add('active');
                }}
            }}

            function filterByCategory(selectedCategory) {{
                const urlParams = new URLSearchParams(window.location.search);
                const currentLeague = urlParams.get('league') || 'all';
                window.location.href = `/?category=${{encodeURIComponent(selectedCategory)}}&league=${{encodeURIComponent(currentLeague)}}`;
            }}

            function filterByLeague(selectedLeague) {{
                const urlParams = new URLSearchParams(window.location.search);
                const currentCategory = urlParams.get('category') || 'all';
                window.location.href = `/?category=${{encodeURIComponent(currentCategory)}}&league=${{encodeURIComponent(selectedLeague)}}`;
            }}
        </script>
    </body>
    </html>
    """
    return html_content
