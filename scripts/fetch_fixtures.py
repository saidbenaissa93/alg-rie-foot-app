import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
TEAM_ID = 1532  # Algérie

DB_PATH = "data/algerie_foot.db"
headers = {"x-apisports-key": API_KEY}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Table pour stocker la liste des matchs à traiter
cursor.execute("""
CREATE TABLE IF NOT EXISTS fixtures (
    fixture_id INTEGER PRIMARY KEY,
    match_date TEXT,
    season INTEGER,
    processed INTEGER DEFAULT 0
)
""")
conn.commit()

seasons = [2021, 2022, 2023, 2024, 2025]

for season in seasons:
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"team": TEAM_ID, "season": season}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("errors"):
        print(f"Erreur saison {season} :", data["errors"])
        continue

    fixtures = data["response"]
    print(f"Saison {season} : {len(fixtures)} matchs trouvés")

    for f in fixtures:
        fixture_id = f["fixture"]["id"]
        match_date = f["fixture"]["date"]
        cursor.execute("""
            INSERT OR IGNORE INTO fixtures (fixture_id, match_date, season, processed)
            VALUES (?, ?, ?, 0)
        """, (fixture_id, match_date, season))

conn.commit()
conn.close()
print("Terminé. Matchs enregistrés dans la table fixtures.")