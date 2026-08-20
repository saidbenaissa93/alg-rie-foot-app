import sqlite3
import re
import unicodedata
import requests
import time
from bs4 import BeautifulSoup
from datetime import date

DB_PATH = "data/algerie_foot.db"
headers = {"User-Agent": "Mozilla/5.0"}

BASE_URL = "https://www.transfermarkt.us/spieler-statistik/wertvollstespieler/marktwertetop/plus/0/ajax/ahrgang/0/land_id/4/kontinent_id/0/jahr/0/yt0/Show/0//page/{page}"

def normalize(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace("-", " ")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", name).strip().lower()

def parse_market_value(text):
    if not text:
        return None
    text = text.replace("€", "").strip()
    if "m" in text:
        return float(text.replace("m", ""))
    elif "k" in text:
        return float(text.replace("k", "")) / 1000
    return None

# --- Préparation de la base ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for column, col_type in [("age", "INTEGER"), ("market_value", "REAL")]:
    try:
        cursor.execute(f"ALTER TABLE player_status ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass

cursor.execute("SELECT id, name FROM players")
existing_by_normalized_name = {normalize(name): pid for pid, name in cursor.fetchall()}

matched = 0
created = 0
total_players = 0

# --- Scraping des pages ---
for page in range(1, 5):
    if total_players >= 100:
        break

    url = BASE_URL.format(page=page)
    print(f"Page {page}...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"class": "items"})
    if not table:
        print(f"  Aucun tableau trouvé sur la page {page}")
        continue

    rows = table.find("tbody").find_all("tr", recursive=False)

    for row in rows:
        if total_players >= 100:
            break

        name_tag = row.find("td", {"class": "hauptlink"})
        if not name_tag:
            continue
        link = name_tag.find("a")
        name = link.get_text(strip=True) if link else None
        if not name:
            continue

        all_tds = row.find_all("td", recursive=False)

        # Structure confirmée : [0]=rang [1]=nom+poste [2]=age [3]=nationalité [4]=club [5]=valeur
        age = None
        if len(all_tds) > 2:
            age_text = all_tds[2].get_text(strip=True)
            if age_text.isdigit():
                age = int(age_text)

        club = None
        if len(all_tds) > 4:
            club_img = all_tds[4].find("img")
            if club_img:
                club = club_img.get("title")

        market_value = None
        if len(all_tds) > 5:
            market_value = parse_market_value(all_tds[5].get_text(strip=True))

        # Poste : cherché dans toute la ligne (pas seulement dans name_tag)
        position = None
        inline_table = row.find("table", {"class": "inline-table"})
        if inline_table:
            rows_inline = inline_table.find_all("tr")
            if len(rows_inline) > 1:
                position = rows_inline[1].get_text(strip=True)

        key = normalize(name)
        player_id = existing_by_normalized_name.get(key)

        if player_id:
            cursor.execute("UPDATE players SET position = COALESCE(?, position) WHERE id = ?",
                            (position, player_id))
            matched += 1
        else:
            cursor.execute("SELECT MIN(id) FROM players")
            min_id = cursor.fetchone()[0] or 0
            player_id = min(min_id, 0) - 1
            cursor.execute("INSERT INTO players (id, name, position) VALUES (?, ?, ?)",
                            (player_id, name, position))
            existing_by_normalized_name[key] = player_id
            created += 1

        cursor.execute("""
            INSERT INTO player_status (player_id, current_club, age, market_value, last_checked)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET
                current_club = excluded.current_club,
                age = excluded.age,
                market_value = excluded.market_value,
                last_checked = excluded.last_checked
        """, (player_id, club, age, market_value, date.today().isoformat()))

        total_players += 1

    conn.commit()
    time.sleep(2)

conn.close()
print(f"\nTotal traité : {total_players}")
print(f"Joueurs mis à jour : {matched}")
print(f"Nouveaux joueurs créés : {created}")