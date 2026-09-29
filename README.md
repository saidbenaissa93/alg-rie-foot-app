# 🇩🇿 Algérie Foot

Site de suivi de l'équipe nationale algérienne de football : effectif, valeurs marchandes, calendrier, résultats, historique en compétitions, records individuels et cartes FIFA.

🔗 **Site en ligne :** déployé automatiquement sur [Vercel](https://vercel.com)

## Comment ça marche

Le projet fonctionne en 3 parties :

1. **Scraping** — des scripts Python (dans `scripts/`) récupèrent les données depuis plusieurs sources :
   - [Transfermarkt](https://www.transfermarkt.us) — valeurs marchandes, âges, clubs actuels
   - [Wikipedia](https://en.wikipedia.org/wiki/Algeria_national_football_team) — calendrier, résultats, historique en compétitions, records
   - [FUTBIN](https://www.futbin.com) — cartes FIFA (mis à jour manuellement, voir plus bas)

2. **Base de données** — toutes les données sont stockées dans `data/algerie_foot.db` (SQLite)

3. **Génération du site** — `scripts/generate_site.py` lit la base et génère `docs/index.html`, un site statique complet (HTML/CSS/JS, sans framework), déployé automatiquement sur Vercel à chaque `git push`

## Automatisation

Un workflow **GitHub Actions** (`.github/workflows/`) tourne automatiquement 2 fois par jour (8h et 20h, heure Algérie) :
1. Relance les scrapers Transfermarkt et Wikipedia
2. Régénère le site
3. Commit et push les changements → Vercel redéploie automatiquement

### Cas particulier : FUTBIN (cartes FIFA)

FUTBIN utilise une protection anti-bot (Cloudflare Turnstile) qui bloque le scraping automatisé depuis le cloud. Ce scraper (`scripts/scrape_futbin.py`) doit donc être lancé **manuellement depuis un PC** de temps en temps :

```bash
python scripts/scrape_futbin.py
python scripts/generate_site.py
git add data/algerie_foot.db docs/index.html
git commit -m "Mise à jour manuelle des cartes FIFA"
git push origin main
```

## Structure du projet

```
scripts/          → tous les scripts Python (scraping, gestion DB, génération du site)
data/             → base de données SQLite
docs/             → site HTML généré (déployé par Vercel)
.github/workflows/→ automatisation GitHub Actions
requirements.txt  → dépendances Python
```

## Lancer le projet en local

```bash
pip install -r requirements.txt
playwright install chromium

# Régénérer le site à partir des données existantes
python scripts/generate_site.py

# Ou relancer un scraper spécifique
python scripts/scrape_wiki_matches.py
```

## Secrets nécessaires (pour l'automatisation GitHub Actions)

Configurés dans **Settings → Secrets and variables → Actions** du repo :

| Secret | Usage |
|---|---|
| `API_FOOTBALL_KEY` | Clé API-Football (statut des joueurs) |
| `PROXY_HOST`, `PROXY_PORT`, `PROXY_USER`, `PROXY_PASS` | Proxy pour contourner les blocages anti-bot sur Transfermarkt |

## Stack technique

- **Python** (requests, BeautifulSoup, Playwright, sqlite3)
- **SQLite** pour le stockage
- **HTML/CSS/JS vanilla** pour le site (pas de framework)
- **GitHub Actions** pour l'automatisation
- **Vercel** pour l'hébergement