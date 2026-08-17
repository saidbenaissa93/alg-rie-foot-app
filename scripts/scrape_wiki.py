import sqlite3
import re
import requests
from bs4 import BeautifulSoup
from datetime import date

DB_PATH = "data/algerie_foot.db"
url = "https://en.wikipedia.org/wiki/Algeria_national_football_team"
headers = {"User-Agent": "Mozilla/5.0"}

POSITIONS = {"GK", "DF", "MF", "FW"}

def normalize(name):
    name = re.sub(r"\(.*?\)", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
rows = soup.find_all("tr", {"class": "nat-fs-player"})
print(f"{len(rows)} lignes trouvées\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM players")
existing_by_normalized_name = {normalize(name): pid for pid, name in cursor.fetchall()}

matched = 0
created = 0
skipped = 0

for row in rows:
    cells = row.find_all("td")
    header = row.find("th")

    if not header or len(cells) < 5:
        skipped += 1
        continue

    name = header.get_text(strip=True)
    first_cell = cells[0].get_text(strip=True)

    if first_cell in POSITIONS:
        # Format "Recent call-ups" : Poste | Naissance | Caps | Buts | Club | ...
        position = first_cell
        birth_text = cells[1].get_text(strip=True)
        club = cells[4].get_text(strip=True)
    else:
        # Format "Effectif actuel" : N° | Poste | Naissance | Caps | Buts | Club
        position =  position = re.sub(r"[^A-Z]", "", cells[1].get_text(strip=True))
        birth_text = cells[2].get_text(strip=True)
        club = cells[5].get_text(strip=True)

    birth_date = birth_text.split("(")[0].strip()

    key = normalize(name)
    player_id = existing_by_normalized_name.get(key)

    if player_id:
        cursor.execute("UPDATE players SET birth_date = ?, position = ? WHERE id = ?",
                        (birth_date, position, player_id))
        matched += 1
    else:
        cursor.execute("SELECT MIN(id) FROM players")
        min_id = cursor.fetchone()[0] or 0
        player_id = min(min_id, 0) - 1
        cursor.execute("INSERT INTO players (id, name, birth_date, position) VALUES (?, ?, ?, ?)",
                        (player_id, name, birth_date, position))
        existing_by_normalized_name[key] = player_id
        created += 1

    cursor.execute("""
        INSERT INTO player_status (player_id, current_club, last_checked)
        VALUES (?, ?, ?)
        ON CONFLICT(player_id) DO UPDATE SET
            current_club = excluded.current_club,
            last_checked = excluded.last_checked
    """, (player_id, club, date.today().isoformat()))

conn.commit()
conn.close()

print(f"Joueurs mis à jour : {matched}")
print(f"Nouveaux joueurs créés : {created}")
print(f"Lignes ignorées : {skipped}")