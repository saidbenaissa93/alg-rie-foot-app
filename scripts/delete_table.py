import sqlite3

DB_PATH = "data/algerie_foot.db"

# Connexion à la base
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Demande du nom de la table à supprimer
table_name = input("Nom de la table à supprimer : ").strip()

# Sécurisation du nom (évite l'injection SQL)
if not table_name.isidentifier():
    print("❌ Nom de table invalide.")
else:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        print(f"✅ Table '{table_name}' supprimée avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de la suppression : {e}")

conn.close()
