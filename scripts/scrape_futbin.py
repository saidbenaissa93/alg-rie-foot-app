from playwright.sync_api import sync_playwright
import sqlite3
import random
import time

DB_PATH = "data/algerie_foot.db"
BASE_URL = "https://www.futbin.com/27/players?page={page}&nation=97&gender=men"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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
    image_url TEXT,        -- visage du joueur
    bg_url TEXT,           -- gabarit de la carte (or, argent, TOTW, Destined for Glory...)
    club_logo_url TEXT,
    nation_flag_url TEXT,
    is_holo INTEGER,       -- 1 si la carte a la classe playercard-27-holo
    rating_color TEXT,     -- variable CSS --ratingColor (couleur du texte rating/poste)
    card_color TEXT        -- variable CSS --cardColor
)
""")
conn.commit()

# Lit tout ce qu'il faut sur la div .playercard-27 d'une ligne :
# classes, variables CSS de couleur, toutes les <img> et tous les background-image.
CARD_JS = r"""
el => {
    const bgOf = n => {
        const m = getComputedStyle(n).backgroundImage.match(/url\("?(.*?)"?\)/);
        return m ? m[1] : null;
    };
    const imgs = [...el.querySelectorAll('img')].map(i => ({
        cls: i.className || '',
        src: i.getAttribute('data-src') || i.getAttribute('data-original') || i.currentSrc || i.getAttribute('src') || ''
    })).filter(i => i.src);
    const bgs = [el, ...el.querySelectorAll('*')].map(bgOf).filter(Boolean);
    return {
        cls: el.className,
        ratingColor: el.style.getPropertyValue('--ratingColor').trim(),
        cardColor: el.style.getPropertyValue('--cardColor').trim(),
        imgs: imgs,
        bgs: bgs,
        html: el.outerHTML
    };
}
"""

seen_kinds = set()   # pour n'afficher qu'un exemple de HTML par type de carte


def img_src(el):
    if not el:
        return None
    return el.get_attribute("data-src") or el.get_attribute("data-original") or el.get_attribute("src")


def classify_layers(meta):
    """Sépare le gabarit de la carte (/cards/) du visage du joueur."""
    urls = [i["src"] for i in meta["imgs"]] + meta["bgs"]
    template = next((u for u in urls if "/cards/" in u), None)

    face = next((u for u in urls if "/players/" in u), None)
    if not face:
        ignored = ("/cards/", "/clubs/", "/nation/", "/flags/")
        face = next((u for u in urls if not any(k in u for k in ignored)), None)
    return template, face


def load_all_images(page):
    """Futbin charge les images au scroll : on descend puis on remonte."""
    for _ in range(6):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(400)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(600)


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

            # --- Carte : type, couleurs, calques ---
            card = row.query_selector(".playercard-27")
            meta = card.evaluate(CARD_JS) if card else None

            is_holo = 1 if meta and "playercard-27-holo" in meta["cls"] else 0
            rating_color = meta["ratingColor"] if meta else None
            card_color = meta["cardColor"] if meta else None

            bg_url, image_url = (None, None)
            if meta:
                bg_url, image_url = classify_layers(meta)

            # Debug : un exemple de HTML par combinaison (holo, couleur)
            kind = (is_holo, rating_color)
            if meta and kind not in seen_kinds and len(seen_kinds) < 6:
                seen_kinds.add(kind)
                print(f"\n=== {name} | holo={is_holo} | ratingColor={rating_color} ===")
                print(f"gabarit: {bg_url}\nvisage : {image_url}")
                print(meta["html"])
                print("=== fin ===\n")

            nation_flag_url = img_src(row.query_selector("img.nation"))
            club_logo_url = img_src(row.query_selector("img[alt='Club']"))

            cursor.execute("""
                INSERT INTO fifa_cards (
                    player_name, rating, position, pace, shooting, passing, dribbling, defending, physical,
                    image_url, bg_url, club_logo_url, nation_flag_url, is_holo, rating_color, card_color
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, int(rating), position, int(pac), int(sho), int(pas), int(dri), int(de), int(phy),
                  image_url, bg_url, club_logo_url, nation_flag_url, is_holo, rating_color, card_color))
            count += 1
            print(f"{name} - {rating} OVR "
                  f"(holo: {'oui' if is_holo else 'non'}, "
                  f"visage: {'OK' if image_url else 'manquant'}, "
                  f"gabarit: {'OK' if bg_url else 'manquant'}, "
                  f"club: {'OK' if club_logo_url else 'manquant'}, "
                  f"nation: {'OK' if nation_flag_url else 'manquant'})")
        except Exception as e:
            print("Erreur sur une ligne :", e)
    return count


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
            load_all_images(page)
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