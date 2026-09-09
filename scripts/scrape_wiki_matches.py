import sqlite3
import re
import requests
from bs4 import BeautifulSoup

DB_PATH = "data/algerie_foot.db"
url = "https://en.wikipedia.org/wiki/Algeria_national_football_team"
headers = {"User-Agent": "Mozilla/5.0"}

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

def find_year_for_table(table):
    for element in table.find_all_previous(["h3", "h2"]):
        text = element.get_text(strip=True)
        if re.fullmatch(r"20\d{2}", text):
            return text
    return None

def parse_date_and_competition(text, table):
    match = re.match(rf"(\d{{1,2}} (?:{MONTHS}) \d{{4}})(.*)", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    match = re.match(rf"(\d{{1,2}} (?:{MONTHS}))(.*)", text)
    if match:
        day_month = match.group(1).strip()
        competition = match.group(2).strip()
        year = find_year_for_table(table)
        if year:
            return f"{day_month} {year}", competition
        return None, None

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

    team1 = tds[1].get_text(strip=True)
    score = tds[2].get_text(strip=True)
    team2 = tds[3].get_text(strip=True)
    venue = tds[4].get_text(strip=True)

    if not match_date:
        # Nettoie toute ancienne entrée incomplète/obsolète pour ce même match
        cursor.execute("""
            DELETE FROM team_matches
            WHERE team1 = ? AND team2 = ? AND venue = ?
            AND (match_date IS NULL OR match_date LIKE 'TBD%')
        """, (team1, team2, venue))
        skipped += 1
        continue

    # Supprime toute ancienne version incomplète (TBD) de ce même match
    cursor.execute("""
        DELETE FROM team_matches
        WHERE team1 = ? AND team2 = ? AND venue = ?
        AND (match_date IS NULL OR match_date LIKE 'TBD%')
    """, (team1, team2, venue))

    cursor.execute("""
        INSERT OR IGNORE INTO team_matches (match_date, competition, team1, score, team2, venue)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (match_date, competition, team1, score, team2, venue))
    count += 1

conn.commit()
conn.close()
print(f"{count} matchs enregistrés (dates complètes)")
print(f"{skipped} lignes ignorées (date incomplète, sans jour)")