import sqlite3

DB_PATH = "data/algerie_foot.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT p.name, p.position, p.birth_date, ps.current_club
    FROM players p
    JOIN player_status ps ON p.id = ps.player_id
    WHERE ps.current_club IS NOT NULL AND ps.current_club != ''
    ORDER BY p.position, p.name
""")

results = cursor.fetchall()
conn.close()

print(f"{len(results)} joueurs déjà sélectionnés et toujours actifs :\n")
for name, position, birth_date, club in results:
    pos = position or "?"
    print(f"[{pos}] {name} - {club}")