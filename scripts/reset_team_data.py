import sqlite3

DB_PATH = "data/algerie_foot.db"

# Connexion à la base
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("🧹 Suppression de toutes les données de la table team_matches...")

# Supprime toutes les lignes
cursor.execute("DELETE FROM team_matches")

# Réinitialise l'auto‑increment (remet l'ID à 1)
cursor.execute("DELETE FROM sqlite_sequence WHERE name='team_matches'")

conn.commit()
conn.close()

print("✅ Toutes les données ont été supprimées, la table est maintenant vide.")