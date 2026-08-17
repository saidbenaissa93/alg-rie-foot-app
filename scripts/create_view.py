import sqlite3

conn = sqlite3.connect("data/algerie_foot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE VIEW IF NOT EXISTS joueurs_complets AS
SELECT 
    p.id,
    p.name,
    p.position,
    p.birth_date,
    ps.current_club,
    ps.last_checked
FROM players p
LEFT JOIN player_status ps ON p.id = ps.player_id
""")

conn.commit()
conn.close()
print("Vue 'joueurs_complets' créée avec succès.")