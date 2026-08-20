import os
import sqlite3
import requests
import time
from dotenv import load_dotenv
from datetime import date

load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
headers = {"x-apisports-key": API_KEY}

DB_PATH = "data/algerie_foot.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Tous les joueurs à ID positif (venant de l'API, donc interrogeables)
cursor.execute("SELECT id, name FROM players WHERE id > 0")
all_players = cursor.fetchall()
print(f"{len(all_players)} joueurs à vérifier\n")

count = 0
for player_id, name in all_players:
    url = "https://v3.football.api-sports.io/players"
    params = {"id": player_id, "season": 2024}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("errors"):
        print(f"Erreur pour {name} :", data["errors"])
        time.sleep(6.5)
        continue

    results = data.get("response", [])
    if results:
        stats = results[0].get("statistics", [])
        club = stats[0]["team"]["name"] if stats else None
        if club:
            cursor.execute("""
                INSERT INTO player_status (player_id, current_club, last_checked)
                VALUES (?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    current_club = excluded.current_club,
                    last_checked = excluded.last_checked
            """, (player_id, club, date.today().isoformat()))
            conn.commit()
            print(f"{name} → {club}")
            count += 1

    time.sleep(6.5)

conn.close()
print(f"\n{count} clubs vérifiés/mis à jour.")