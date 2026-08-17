import sqlite3

DB_PATH = "data/algerie_foot.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Table des joueurs (infos fixes)
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    birth_date TEXT,
    position TEXT
)
""")

# Table des sélections (une ligne = une apparition en sélection)
cursor.execute("""
CREATE TABLE IF NOT EXISTS caps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    fixture_id INTEGER NOT NULL,
    match_date TEXT,
    FOREIGN KEY (player_id) REFERENCES players(id)
)
""")

# Table du statut actuel des joueurs (mise à jour régulière)
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_status (
    player_id INTEGER PRIMARY KEY,
    current_club TEXT,
    last_checked TEXT,
    FOREIGN KEY (player_id) REFERENCES players(id)
)
""")

conn.commit()
conn.close()

print("Base de données initialisée avec succès dans", DB_PATH)