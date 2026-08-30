from playwright.sync_api import sync_playwright
import sqlite3
import random
import time

DB_PATH = "data/algerie_foot.db"
BASE_URL = "https://www.futbin.com/27/players?page={page}&nation=97&gender=men"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS fifa_cards")
cursor.execute("""
CREATE TABLE fifa_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT,
    rating INTEGER,
    position TEXT,
    pace INTEGER,
    shooting INTEGER,
    passing INTEGER,
    dribbling INTEGER,
    defending INTEGER,
    physical INTEGER,
    image_url TEXT,
    bg_url TEXT,
    club_logo_url TEXT,
    nation_flag_url TEXT
)
""")
conn.commit()

def scrape_rows(page):
    rows = page.query_selector_all("table tbody tr")
    count = 0
    for row in rows:
        cells = row.query_selector_all("td")
        if len(cells) < 16:
            continue
        try:
            name_block = cells[0].inner_text().split("\n")
            name = name_block[1].strip() if len(name_block) > 1 else name_block[0].strip()
            rating = cells[1].inner_text().strip()
            position = cells[3].inner_text().split("\n")[0].strip()
            pac = cells[10].inner_text().strip()
            sho = cells[11].inner_text().strip()
            pas = cells[12].inner_text().strip()
            dri = cells[13].inner_text().strip()
            de = cells[14].inner_text().strip()
            phy = cells[15].inner_text().strip()

            img_el = row.query_selector(".playercard-s-base-img")
            image_url = img_el.get_attribute("src") if img_el else None

            bg_el = row.query_selector(".playercard-s-27-bg")
            bg_url = bg_el.get_attribute("src") if bg_el else None

            nation_el = row.query_selector("img.nation")
            nation_flag_url = nation_el.get_attribute("src") if nation_el else None

            club_el = row.query_selector("img[alt='Club']")
            club_logo_url = club_el.get_attribute("src") if club_el else None

            cursor.execute("""
                INSERT INTO fifa_cards (player_name, rating, position, pace, shooting, passing, dribbling, defending, physical, image_url, bg_url, club_logo_url, nation_flag_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, int(rating), position, int(pac), int(sho), int(pas), int(dri), int(de), int(phy), image_url, bg_url, club_logo_url, nation_flag_url))
            count += 1
            print(f"{name} - {rating} OVR (club: {'OK' if club_logo_url else 'manquant'}, nation: {'OK' if nation_flag_url else 'manquant'})")
        except Exception as e:
            print("Erreur sur une ligne :", e)
    return count

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    total = 0
    for page_num in range(1, 4):
        print(f"\n--- Page {page_num} ---")

        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 800})
        page = context.new_page()

        url = BASE_URL.format(page=page_num)
        page.goto(url, timeout=30000, wait_until="domcontentloaded")

        try:
            page.wait_for_selector("table tbody tr", timeout=15000)
            page.wait_for_timeout(2000)
            found = scrape_rows(page)
            conn.commit()
            total += found
        except Exception as e:
            print(f"Échec page {page_num} :", e)
            page.screenshot(path=f"debug_page{page_num}.png")
            found = 0

        context.close()

        if page_num < 3:
            pause = random.uniform(20, 35)
            print(f"Pause de {pause:.0f}s avant la page suivante...")
            time.sleep(pause)

    browser.close()

conn.close()
print(f"\n{total} cartes enregistrées au total")