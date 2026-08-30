import sqlite3
import requests
from bs4 import BeautifulSoup

DB_PATH = "data/algerie_foot.db"
url = "https://en.wikipedia.org/wiki/Algeria_national_football_team"
headers = {"User-Agent": "Mozilla/5.0"}

COLUMNS = ["year", "round", "position", "played", "wins", "draws", "losses", "goals_for", "goals_against"]
TARGET_COMPETITIONS = ["FIFA World Cup", "Africa Cup of Nations"]
EXCLUDED_ROUNDS = {
    "Did not qualify", "Did not enter", "Not a FIFA member",
    "Withdrew", "Banned", "To be determined", "Total"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS competition_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition TEXT,
    year TEXT,
    round TEXT,
    position TEXT,
    played TEXT,
    wins TEXT,
    draws TEXT,
    losses TEXT,
    goals_for TEXT,
    goals_against TEXT
)
""")
conn.commit()

def parse_table_with_rowspan(table, num_cols):
    rows = table.find("tbody").find_all("tr")
    carry_over = {}
    results = []

    for row in rows:
        raw_cells = row.find_all(["td", "th"])
        full_row = []
        col_index = 0
        raw_index = 0

        while len(full_row) < num_cols:
            if col_index in carry_over and carry_over[col_index][1] > 0:
                value, remaining = carry_over[col_index]
                full_row.append(value)
                carry_over[col_index] = (value, remaining - 1)
                col_index += 1
                continue

            if raw_index >= len(raw_cells):
                full_row.append(None)
                col_index += 1
                continue

            cell = raw_cells[raw_index]
            text = cell.get_text(strip=True)
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))

            for _ in range(colspan):
                if len(full_row) >= num_cols:
                    break
                full_row.append(text)
                if rowspan > 1:
                    carry_over[col_index] = (text, rowspan - 1)
                col_index += 1

            raw_index += 1

        results.append(full_row)
    return results

section = soup.find("section", {"id": "mwAzc"})
if not section:
    print("Section 'Competitive record' introuvable")
else:
    headings = section.find_all(["h3"])
    total = 0
    skipped = 0

    for h in headings:
        competition_name = h.get_text(strip=True).replace("[edit]", "").strip()

        if competition_name not in TARGET_COMPETITIONS:
            continue

        table = None
        for sib in h.find_all_next():
            if sib.name == "table" and "wikitable" in (sib.get("class") or []):
                table = sib
                break
            if sib.name == "h3":
                break

        if not table:
            continue

        rows_data = parse_table_with_rowspan(table, len(COLUMNS))
        for row in rows_data[1:]:
            if not row[0]:
                continue

            round_value = (row[1] or "").strip()
            if any(excluded in round_value for excluded in EXCLUDED_ROUNDS):
                skipped += 1
                continue

            values = (competition_name, *row[:9])
            cursor.execute(f"""
                INSERT INTO competition_history
                (competition, {', '.join(COLUMNS)})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)
            total += 1

    conn.commit()
    print(f"{total} lignes enregistrées, {skipped} lignes exclues (non-participation)")

conn.close()