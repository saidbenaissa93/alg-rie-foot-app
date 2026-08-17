import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
headers = {"x-apisports-key": API_KEY}

url = "https://v3.football.api-sports.io/fixtures"
params = {"team": 1532, "last": 20}

response = requests.get(url, headers=headers, params=params)
data = response.json()

if data.get("errors"):
    print("Erreur :", data["errors"])
else:
    for f in data["response"]:
        print(f["fixture"]["date"], "-", f["fixture"]["id"])