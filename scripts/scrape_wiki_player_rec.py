import sqlite3
import requests
from bs4 import BeautifulSoup

DB_PATH = "data/algerie_foot.db"
url = "https://en.wikipedia.org/wiki/Algeria_national_football_team"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DELETE FROM individual_records")
conn.commit()

def find_table_after_heading(heading_text):
    """Cherche un h3 (ou h4) dont le texte contient heading_text, puis renvoie
    le premier tableau wikitable qui suit. Recherche par TEXTE plutôt que par
    ID auto-généré (type 'mwAms'), car ces ID changent dès que la page
    Wikipedia est modifiée alors que le texte du titre, lui, reste stable."""
    for heading in soup.find_all(["h3", "h4"]):
        if heading_text.lower() in heading.get_text(strip=True).lower():
            for sib in heading.find_all_next():
                if sib.name == "table" and "wikitable" in (sib.get("class") or []):
                    return sib
                if sib.name in ("h2", "h3"):
                    break
    return None

def scrape_record_table(table, record_type):
    if not table:
        print(f"Tableau introuvable pour '{record_type}'")
        return 0

    rows = table.find("tbody").find_all("tr")[1:]  # on saute l'en-tête

    carry_over = {}
    count = 0

    for row in rows:
        raw_cells = row.find_all(["td", "th"])
        full_row = []
        col_index = 0
        raw_index = 0

        while len(full_row) < 4:
            if col_index in carry_over and carry_over[col_index][1] > 0:
                value, remaining = carry_over[col_index]
                full_row.append(value)
                carry_over[col_index] = (value, remaining - 1)
                col_index += 1
                continue

            if raw_index >= len(raw_cells):
                break

            cell = raw_cells[raw_index]
            text = cell.get_text(strip=True)
            rowspan = int(cell.get("rowspan", 1))

            full_row.append(text)
            if rowspan > 1:
                carry_over[col_index] = (text, rowspan - 1)

            raw_index += 1
            col_index += 1

        if len(full_row) < 4:
            continue

        rank_text, player_name, value_text, career = full_row[0], full_row[1], full_row[2], full_row[3]
        rank = int(rank_text) if rank_text.isdigit() else None
        value = int(value_text) if value_text.isdigit() else None

        cursor.execute("""
            INSERT OR IGNORE INTO individual_records (record_type, rank, player_name, value, career)
            VALUES (?, ?, ?, ?, ?)
        """, (record_type, rank, player_name, value, career))
        count += 1

    conn.commit()
    return count

appearances_table = find_table_after_heading("Most appearances")
n1 = scrape_record_table(appearances_table, "appearances")
print(f"{n1} joueurs enregistrés pour 'Most appearances'")

goals_table = find_table_after_heading("Top goalscorers")
n2 = scrape_record_table(goals_table, "goals")
print(f"{n2} joueurs enregistrés pour 'Top goalscorers'")

conn.close()