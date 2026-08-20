import sqlite3

conn = sqlite3.connect("data/algerie_foot.db")
cursor = conn.cursor()

cursor.execute("DROP VIEW IF EXISTS joueurs_complets")

cursor.execute("""
CREATE VIEW joueurs_complets AS
SELECT
    p.id,
    p.name,
    p.position,
    ps.age,
    ps.current_club,
    ps.market_value,
    ps.last_checked
FROM players p
LEFT JOIN player_status ps ON p.id = ps.player_id
ORDER BY ps.market_value DESC
""")

conn.commit()
conn.close()
print("Vue 'joueurs_complets' créée avec succès.")