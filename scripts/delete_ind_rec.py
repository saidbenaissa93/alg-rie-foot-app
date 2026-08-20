import sqlite3

DB_PATH = "data/algerie_foot.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Reset de la table : individual_records")

# Supprime toutes les lignes
cursor.execute("DELETE FROM individual_records")

# Reset de l'auto-increment
cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'individual_records'")

conn.commit()
conn.close()

print("La table 'individual_records' a été vidée et l'auto-increment réinitialisé.")
