import sqlite3

conn = sqlite3.connect("data/algerie_foot.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM player_status")
cursor.execute("DELETE FROM players ")
cursor.execute("UPDATE players SET birth_date = NULL, position = NULL")

conn.commit()
conn.close()
print("Base nettoyée : player_status vidée, joueurs scrapés (id<0) supprimés, birth_date/position réinitialisés")