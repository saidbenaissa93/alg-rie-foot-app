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
HEADER_LABELS = {"year", "round", "position", "pld", "w", "d", "l", "gf", "ga"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS competition_history")
cursor.execute("""
CREATE TABLE competition_history (
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

def is_header_row(row):
    if not row or not row[0]:
        return False
    first_cell = row[0].strip().lower()
    return first_cell in HEADER_LABELS

# --- Recherche robuste de la section "Competitive record" ---
# On cherche par TEXTE du titre plutôt que par ID auto-généré par Wikipedia
# (ces ID type "mwAzc" changent dès que l'article est modifié, donc
# fragiles à long terme — le texte du titre, lui, change rarement).
headings = []
target_h2 = None
for h2 in soup.find_all("h2"):
    if "Competitive record" in h2.get_text():
        target_h2 = h2
        break

if not target_h2:
    print("Section 'Competitive record' introuvable")
else:
    # On collecte tous les h3 qui suivent ce h2, jusqu'au prochain h2
    for sib in target_h2.find_all_next():
        if sib.name == "h2":
            break
        if sib.name == "h3":
            headings.append(sib)

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

        if is_header_row(row):
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