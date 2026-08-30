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

def scrape_record_table(table_id, record_type):
    table = soup.find("table", {"id": table_id})
    if not table:
        print(f"Tableau '{table_id}' introuvable")
        return 0

    rows = table.find("tbody").find_all("tr")[1:]  # on saute l'en-tête

    # Mémorise les cellules en cours de "rowspan" par position de colonne
    carry_over = {}  # {colonne_index: (valeur, lignes_restantes)}
    count = 0

    for row in rows:
        raw_cells = row.find_all(["td", "th"])
        full_row = []
        col_index = 0
        raw_index = 0

        # Reconstruit la ligne complète en tenant compte des rowspans actifs
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

n1 = scrape_record_table("mwAms", "appearances")
print(f"{n1} joueurs enregistrés pour 'Most appearances'")

# Pour "Top goalscorers", il faut trouver l'id de CE tableau précis
goals_section = soup.find("section", {"id": "mwAr4"})
goals_table = goals_section.find("table", {"class": "wikitable"}) if goals_section else None
goals_table_id = goals_table.get("id") if goals_table else None

if goals_table_id:
    n2 = scrape_record_table(goals_table_id, "goals")
    print(f"{n2} joueurs enregistrés pour 'Top goalscorers'")
else:
    print("Tableau 'Top goalscorers' introuvable")

conn.close()