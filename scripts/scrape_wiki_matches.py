import sqlite3
import re
import requests
from bs4 import BeautifulSoup

DB_PATH = "data/algerie_foot.db"
url = "https://en.wikipedia.org/wiki/Algeria_national_football_team"
headers = {"User-Agent": "Mozilla/5.0"}

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

def find_year_for_table(table):
    """Remonte dans le HTML pour trouver le titre d'année (h3/h2) le plus proche avant ce tableau."""
    for element in table.find_all_previous(["h3", "h2"]):
        text = element.get_text(strip=True)
        if re.fullmatch(r"20\d{2}", text):
            return text
    return None

def parse_date_and_competition(text, table):
    """
    Ne garde que les dates complètes (jour + mois [+ année]).
    Retourne (match_date, competition) ou (None, None) si la date est incomplète.
    """
    # Cas : "25 September 2027 ..." (jour + mois + année déjà présents)
    match = re.match(rf"(\d{{1,2}} (?:{MONTHS}) \d{{4}})(.*)", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Cas : "23 September ..." (jour + mois, année à déduire du titre de section)
    match = re.match(rf"(\d{{1,2}} (?:{MONTHS}))(.*)", text)
    if match:
        day_month = match.group(1).strip()
        competition = match.group(2).strip()
        year = find_year_for_table(table)
        if year:
            return f"{day_month} {year}", competition
        return None, None  # pas d'année trouvable, on ignore la ligne

    # Cas : "November 2027 ..." (mois seul, sans jour) → toujours ignoré
    return None, None

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
skipped = 0
for t in tables:
    row = t.find("tr", style=lambda s: s and "vertical-align:top" in s)
    if not row:
        continue
    tds = row.find_all("td", recursive=False)
    if len(tds) < 5:
        continue

    raw_text = tds[0].get_text(strip=True)
    match_date, competition = parse_date_and_competition(raw_text, t)

    if not match_date:
        skipped += 1
        continue

    team1 = tds[1].get_text(strip=True)
    score = tds[2].get_text(strip=True)
    team2 = tds[3].get_text(strip=True)
    venue = tds[4].get_text(strip=True)

    cursor.execute("""
        INSERT OR IGNORE INTO team_matches (match_date, competition, team1, score, team2, venue)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (match_date, competition, team1, score, team2, venue))
    count += 1

conn.commit()
conn.close()
print(f"{count} matchs enregistrés (dates complètes)")
print(f"{skipped} lignes ignorées (date incomplète, sans jour)")