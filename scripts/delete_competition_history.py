import sqlite3

conn = sqlite3.connect("data/algerie_foot.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS competition_history")
conn.commit()
conn.close()
print("Table 'competition_history' supprimée")