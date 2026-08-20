import sqlite3

DB_PATH = "data/algerie_foot.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Dates exactes trouvées pour les qualifs CAN 2027
updates = [
    ("Algeria", "Zambia", "23 September 2026"),
    ("Burundi", "Algeria", "27 September 2026"),
    ("Algeria", "Togo", "11 November 2026"),
    ("Togo", "Algeria", "15 November 2026"),
    ("Zambia", "Algeria", "24 March 2027"),
    ("Algeria", "Burundi", "28 March 2027"),
]

count = 0
for team1, team2, match_date in updates:
    cursor.execute("""
        UPDATE team_matches
        SET match_date = ?
        WHERE team1 = ? AND team2 = ?
    """, (match_date, team1, team2))
    count += cursor.rowcount

conn.commit()
conn.close()
print(f"{count} lignes mises à jour avec les vraies dates AFCON 2027")