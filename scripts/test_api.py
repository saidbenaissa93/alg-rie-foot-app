print("Le script démarre")

import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")

TEAM_ID = 1532  # Algérie (sélection A)

url = f"https://v3.football.api-sports.io/players/squads?team={TEAM_ID}"
headers = {"x-apisports-key": API_KEY}

response = requests.get(url, headers=headers)
data = response.json()

if data.get("errors"):
    print("Erreur API :", data["errors"])
else:
    players = data["response"][0]["players"]
    print(f"Nombre de joueurs trouvés : {len(players)}\n")
    for p in players:
        print(f"{p['name']} - {p['position']} - {p['age']} ans")