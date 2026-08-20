import sqlite3
import re
import requests
from bs4 import BeautifulSoup

DB_PATH = "data/algerie_foot.db"
url = "https://en.wikipedia.org/wiki/Algeria_national_football_team"
headers = {"User-Agent": "Mozilla/5.0"}

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

def split_date_competition(text):
    match = re.match(rf"(\d{{1,2}} (?:{MONTHS}))(.*)", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, text.strip()

def find_year_for_table(table):
    """Remonte dans le HTML pour trouver le titre d'année (h3) le plus proche avant ce tableau."""
    for element in table.find_all_previous(["h3", "h2"]):
        text = element.get_text(strip=True)
        if re.fullmatch(r"20\d{2}", text):
            return text
    return None

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

tables = soup.find_all("table", {"class": "vevent"})
print(f"{len(tables)} matchs trouvés\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS team_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_date TEXT,
    competition TEXT,
    team1 TEXT,
    score TEXT,
    team2 TEXT,
    venue TEXT,
    UNIQUE(match_date, team1, team2, venue)
)
""")
conn.commit()

count = 0
for t in tables:
    row = t.find("tr", style=lambda s: s and "vertical-align:top" in s)
    if not row:
        continue
    tds = row.find_all("td", recursive=False)
    if len(tds) < 5:
        continue

    raw_text = tds[0].get_text(strip=True)
    day_month, competition = split_date_competition(raw_text)
    team1 = tds[1].get_text(strip=True)
    score = tds[2].get_text(strip=True)
    team2 = tds[3].get_text(strip=True)
    venue = tds[4].get_text(strip=True)

    year = find_year_for_table(t)

    if day_month and year:
        match_date = f"{day_month} {year}"
    elif day_month:
        match_date = day_month  # au cas où l'année ne serait pas trouvée
    else:
        match_date = None  # cas "TBD"

    cursor.execute("""
        INSERT OR IGNORE INTO team_matches (match_date, competition, team1, score, team2, venue)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (match_date, competition, team1, score, team2, venue))
    count += 1

conn.commit()
conn.close()
print(f"{count} matchs enregistrés (doublons ignorés)")