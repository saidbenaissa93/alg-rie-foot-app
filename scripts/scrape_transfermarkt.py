from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import sqlite3
import re
import unicodedata
import time
import os
from datetime import date

DB_PATH = "data/algerie_foot.db"

PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
USE_PROXY = os.getenv("USE_PROXY", "true") == "true"

proxy_config = None
if USE_PROXY and PROXY_HOST and PROXY_PORT:
    proxy_config = {
        "server": f"http://{PROXY_HOST}:{PROXY_PORT}",
        "username": PROXY_USER,
        "password": PROXY_PASS,
    }

BASE_URL = "https://www.transfermarkt.us/spieler-statistik/wertvollstespieler/marktwertetop/plus/0/ajax/ahrgang/0/land_id/4/kontinent_id/0/jahr/0/yt0/Show/0//page/{page}"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

EXTRACT_ROWS_JS = """
() => {
    const table = document.querySelector('table.items');
    if (!table) return null;
    const tbody = table.querySelector('tbody');
    if (!tbody) return null;
    const rows = Array.from(tbody.children).filter(el => el.tagName === 'TR');
    return rows.map(row => {
        const tds = Array.from(row.children).filter(el => el.tagName === 'TD');
        const nameLink = row.querySelector('td.hauptlink a');
        const name = nameLink ? nameLink.textContent.trim() : null;
        const age = tds[2] ? tds[2].textContent.trim() : null;
        let club = null;
        if (tds[4]) {
            const img = tds[4].querySelector('img');
            club = img ? img.getAttribute('title') : null;
        }
        const marketValueText = tds[5] ? tds[5].textContent.trim() : null;
        let position = null;
        const inline = row.querySelector('table.inline-table');
        if (inline) {
            const irows = inline.querySelectorAll('tr');
            if (irows.length > 1) {
                position = irows[1].textContent.trim();
            }
        }
        return { name, age, club, marketValueText, position };
    });
}
"""

def normalize(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace("-", " ")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", name).strip().lower()

def parse_market_value(text):
    if not text:
        return None
    text = text.replace("€", "").strip()
    if "m" in text:
        return float(text.replace("m", ""))
    elif "k" in text:
        return float(text.replace("k", "")) / 1000
    return None

# --- Préparation de la base ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for column, col_type in [("age", "INTEGER"), ("market_value", "REAL")]:
    try:
        cursor.execute(f"ALTER TABLE player_status ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass

cursor.execute("SELECT id, name FROM players")
existing_by_normalized_name = {normalize(name): pid for pid, name in cursor.fetchall()}

matched = 0
created = 0
total_players = 0

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, proxy=proxy_config)

    for page_num in range(1, 5):
        if total_players >= 100:
            break

        print(f"Page {page_num}...")

        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 800})
        page = context.new_page()
        stealth_sync(page)

        url = BASE_URL.format(page=page_num)
        page.goto(url, timeout=30000, wait_until="domcontentloaded")

        try:
            page.wait_for_selector("table.items tbody tr", timeout=15000)
            page.wait_for_timeout(1500)
            rows_data = page.evaluate(EXTRACT_ROWS_JS)
        except Exception as e:
            print(f"  Aucun tableau trouvé sur la page {page_num} : {e}")
            try:
                print(f"  Titre de la page : {page.title()}")
                print(f"  Aperçu du HTML : {page.content()[:500]}")
            except Exception as inner_e:
                print(f"  Impossible de lire le contenu de la page : {inner_e}")
            rows_data = None

        context.close()

        if not rows_data:
            time.sleep(2)
            continue

        for row in rows_data:
            if total_players >= 100:
                break

            name = row.get("name")
            if not name:
                continue

            age = None
            age_text = row.get("age")
            if age_text and age_text.isdigit():
                age = int(age_text)

            club = row.get("club")
            market_value = parse_market_value(row.get("marketValueText"))
            position = row.get("position")

            key = normalize(name)
            player_id = existing_by_normalized_name.get(key)

            if player_id:
                cursor.execute("UPDATE players SET position = COALESCE(?, position) WHERE id = ?",
                                (position, player_id))
                matched += 1
            else:
                cursor.execute("SELECT MIN(id) FROM players")
                min_id = cursor.fetchone()[0] or 0
                player_id = min(min_id, 0) - 1
                cursor.execute("INSERT INTO players (id, name, position) VALUES (?, ?, ?)",
                                (player_id, name, position))
                existing_by_normalized_name[key] = player_id
                created += 1

            cursor.execute("""
                INSERT INTO player_status (player_id, current_club, age, market_value, last_checked)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    current_club = excluded.current_club,
                    age = excluded.age,
                    market_value = excluded.market_value,
                    last_checked = excluded.last_checked
            """, (player_id, club, age, market_value, date.today().isoformat()))

            total_players += 1

        conn.commit()
        time.sleep(2)

    browser.close()

conn.close()
print(f"\nTotal traité : {total_players}")
print(f"Joueurs mis à jour : {matched}")
print(f"Nouveaux joueurs créés : {created}")