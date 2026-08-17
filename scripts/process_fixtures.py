import os
import sqlite3
import requests
from dotenv import load_dotenv
import time

load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
DB_PATH = "data/algerie_foot.db"
headers = {"x-apisports-key": API_KEY}

MAX_REQUESTS_PER_RUN = 90  # marge de sécurité sous les 100/jour

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Récupère les matchs pas encore traités
cursor.execute("SELECT fixture_id, match_date FROM fixtures WHERE processed = 0")
to_process = cursor.fetchall()

print(f"{len(to_process)} matchs restants à traiter")

count = 0
for fixture_id, match_date in to_process:
    if count >= MAX_REQUESTS_PER_RUN:
        print("Limite de requêtes atteinte pour cette exécution, on s'arrête ici.")
        break

    url = "https://v3.football.api-sports.io/fixtures/players"
    params = {"fixture": fixture_id}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    count += 1

    if data.get("errors"):
        print(f"Erreur fixture {fixture_id} :", data["errors"])
        continue

    # data["response"] contient les 2 équipes, on cherche l'Algérie
    for team_data in data["response"]:
        if team_data["team"]["id"] != 1532:
            continue  # on ignore l'équipe adverse

        for player_entry in team_data["players"]:
            p = player_entry["player"]
            player_id = p["id"]
            player_name = p["name"]

            # Insère le joueur s'il n'existe pas encore
            cursor.execute("""
                INSERT OR IGNORE INTO players (id, name) VALUES (?, ?)
            """, (player_id, player_name))

            # Insère la sélection (le "cap")
            cursor.execute("""
                INSERT INTO caps (player_id, fixture_id, match_date) VALUES (?, ?, ?)
            """, (player_id, fixture_id, match_date))

    # Marque le match comme traité
    cursor.execute("UPDATE fixtures SET processed = 1 WHERE fixture_id = ?", (fixture_id,))
    conn.commit()  # on sauvegarde au fur et à mesure, pas à la fin

    print(f"Match {fixture_id} traité ({count}/{len(to_process)})")
    time.sleep(6.5)  # petite pause pour ne pas spammer l'API

conn.close()
print("Terminé pour cette exécution.")