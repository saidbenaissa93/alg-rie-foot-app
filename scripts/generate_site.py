import sqlite3
import json

DB_PATH = "data/algerie_foot.db"
OUTPUT_PATH = "site/index.html"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT name, position, age, current_club, market_value
    FROM joueurs_complets
    WHERE current_club IS NOT NULL
    ORDER BY market_value DESC
""")
players = [
    {"name": r[0], "position": r[1], "age": r[2], "club": r[3], "value": r[4]}
    for r in cursor.fetchall()
]

cursor.execute("""
    SELECT match_date, competition, team1, score, team2, venue
    FROM team_matches
    ORDER BY id
""")
matches = [
    {"date": r[0], "competition": r[1], "team1": r[2], "score": r[3], "team2": r[4], "venue": r[5]}
    for r in cursor.fetchall()
]

cursor.execute("""
    SELECT record_type, rank, player_name, value, career
    FROM individual_records
    ORDER BY record_type, rank
""")
records = [
    {"type": r[0], "rank": r[1], "player": r[2], "value": r[3], "career": r[4]}
    for r in cursor.fetchall()
]

cursor.execute("""
    SELECT competition, year, round, position, played, wins, draws, losses, goals_for, goals_against
    FROM competition_history
    ORDER BY competition, id
""")
competitions = [
    {"competition": r[0], "year": r[1], "round": r[2], "position": r[3],
     "played": r[4], "wins": r[5], "draws": r[6], "losses": r[7], "gf": r[8], "ga": r[9]}
    for r in cursor.fetchall()
]

cursor.execute("""
    SELECT player_name, rating, position, pace, shooting, passing, dribbling, defending, physical, image_url, bg_url, club_logo_url, nation_flag_url
    FROM fifa_cards
    ORDER BY rating DESC
""")
fifa_cards = [
    {"name": r[0], "rating": r[1], "position": r[2], "pac": r[3], "sho": r[4],
     "pas": r[5], "dri": r[6], "de": r[7], "phy": r[8], "image": r[9], "bg": r[10],
     "club_logo": r[11], "nation_flag": r[12]}
    for r in cursor.fetchall()
]

conn.close()

data_json = json.dumps({
    "players": players, "matches": matches, "records": records,
    "competitions": competitions, "fifa_cards": fifa_cards
}, ensure_ascii=False)

html_template = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Algérie Foot</title>
<style>
    body { font-family: -apple-system, Arial, sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 0; }

    .flag-banner { position: relative; display: flex; height: 140px; width: 100%; }
    .flag-banner .half { flex: 1; }
    .flag-banner .half.green { background: #006233; }
    .flag-banner .half.white { background: #f2f2ee; }
    .flag-banner svg {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 110px;
        height: 110px;
    }

    nav { display: flex; justify-content: center; background: #161b22; border-bottom: 1px solid #30363d; flex-wrap: wrap; }
    nav button { background: none; border: none; color: #8b949e; padding: 14px 20px; font-size: 15px; cursor: pointer; border-bottom: 3px solid transparent; }
    nav button.active { color: #fff; border-bottom-color: #d21034; }
    .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
    .tab { display: none; }
    .tab.active { display: block; }
    input[type="text"] { width: 100%; padding: 10px; margin-bottom: 16px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; box-sizing: border-box; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
    th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #21262d; font-size: 14px; }
    th { background: #161b22; color: #8b949e; cursor: pointer; position: sticky; top: 0; }
    tr:hover { background: #161b22; }
    .value { color: #3fb950; font-weight: 600; }
    .win { border-left: 3px solid #3fb950; }
    .loss { border-left: 3px solid #f85149; }
    .draw { border-left: 3px solid #d29922; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; background: #21262d; }
    h2 { border-bottom: 2px solid #d21034; padding-bottom: 6px; margin-top: 32px; }
    h2:first-child { margin-top: 0; }

    #fifaCards { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 20px; }
    .fifa-card-wrapper { background: #161b22; border-radius: 10px; padding: 12px; text-align: center; }
    .fifa-card { position: relative; width: 130px; height: 165px; margin: 0 auto; }
    .fifa-card img.bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
    .fifa-card img.photo { position: absolute; top: 20%; left: 50%; transform: translateX(-50%); width: 55%; z-index: 2; }
    .fifa-card .rating-text { position: absolute; top: 30px; left: 14px; font-weight: 800; font-size: 20px; line-height: 1; color: #3a2a0d; z-index: 3; text-align: center; }
    .fifa-card .pos-text { position: absolute; top: 55px; left: 14px; font-size: 11px; line-height: 1; color: #3a2a0d; font-weight: 700; z-index: 3; text-align: center; }
    .fifa-card-name { font-size: 13px; margin-top: 8px; font-weight: 600; }
    .fifa-badges { display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 6px; }
    .fifa-badges img { height: 18px; width: auto; }
    .fifa-stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3px 8px; font-size: 11px; margin-top: 8px; text-align: left; color: #8b949e; }
    .fifa-stats-grid b { color: #e6edf3; }
</style>
</head>
<body>

<div class="flag-banner">
    <div class="half green"></div>
    <div class="half white"></div>
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M 62 20 A 32 32 0 1 0 62 80 A 26 26 0 1 1 62 20 Z" fill="#D21034"/>
        <path d="M50 38 L53.5 48.5 L64.5 48.5 L55.7 55 L59 65.5 L50 59 L41 65.5 L44.3 55 L35.5 48.5 L46.5 48.5 Z" fill="#D21034"/>
    </svg>
</div>

<nav>
    <button class="tab-btn active" data-tab="players">Joueurs</button>
    <button class="tab-btn" data-tab="matches">Calendrier &amp; Résultats</button>
    <button class="tab-btn" data-tab="records">Records</button>
    <button class="tab-btn" data-tab="competitions">Compétitions</button>
    <button class="tab-btn" data-tab="fifa">Cartes FIFA</button>
</nav>

<div class="container">

    <div id="players" class="tab active">
        <input type="text" id="playerSearch" placeholder="Rechercher un joueur, club, poste...">
        <table id="playersTable">
            <thead>
                <tr>
                    <th data-key="name">Joueur</th>
                    <th data-key="position">Poste</th>
                    <th data-key="age">Âge</th>
                    <th data-key="club">Club</th>
                    <th data-key="value">Valeur (M€)</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <div id="matches" class="tab">
        <input type="text" id="matchSearch" placeholder="Rechercher une compétition, un adversaire...">

        <h2>Prochains matchs</h2>
        <table id="upcomingTable">
            <thead><tr><th>Date</th><th>Compétition</th><th>Match</th><th>Lieu</th></tr></thead>
            <tbody></tbody>
        </table>

        <h2>Derniers résultats</h2>
        <table id="resultsTable">
            <thead><tr><th>Date</th><th>Compétition</th><th>Match</th><th>Lieu</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <div id="records" class="tab">
        <h2>Meilleurs sélectionnés</h2>
        <table id="appearancesTable">
            <thead><tr><th>Rang</th><th>Joueur</th><th>Sélections</th><th>Carrière</th></tr></thead>
            <tbody></tbody>
        </table>
        <h2>Meilleurs buteurs</h2>
        <table id="goalsTable">
            <thead><tr><th>Rang</th><th>Joueur</th><th>Buts</th><th>Carrière</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <div id="competitions" class="tab">
        <h2>Coupe du Monde</h2>
        <table id="worldCupTable">
            <thead><tr><th>Année</th><th>Résultat</th><th>Pos.</th><th>J</th><th>V</th><th>N</th><th>D</th><th>BP</th><th>BC</th></tr></thead>
            <tbody></tbody>
        </table>
        <h2>Coupe d'Afrique des Nations</h2>
        <table id="afconTable">
            <thead><tr><th>Année</th><th>Résultat</th><th>Pos.</th><th>J</th><th>V</th><th>N</th><th>D</th><th>BP</th><th>BC</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <div id="fifa" class="tab">
        <div id="fifaCards"></div>
    </div>

</div>

<script>
const DATA = __DATA_JSON__;

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
    });
});

function renderPlayers(list) {
    const tbody = document.querySelector('#playersTable tbody');
    tbody.innerHTML = list.map(p => `
        <tr>
            <td>${p.name}</td>
            <td><span class="badge">${p.position || '-'}</span></td>
            <td>${p.age || '-'}</td>
            <td>${p.club || '-'}</td>
            <td class="value">${p.value ? p.value.toFixed(2) : '-'}</td>
        </tr>
    `).join('');
}
renderPlayers(DATA.players);

document.getElementById('playerSearch').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    renderPlayers(DATA.players.filter(p =>
        (p.name||'').toLowerCase().includes(q) ||
        (p.club||'').toLowerCase().includes(q) ||
        (p.position||'').toLowerCase().includes(q)
    ));
});

function matchRowHTML(m) {
    let cls = '';
    if (m.score && m.score.includes('–')) {
        const parts = m.score.replace(/\\(.*?\\)/g, '').split('–').map(s => parseInt(s));
        if (!isNaN(parts[0]) && !isNaN(parts[1])) {
            const algeriaHome = m.team1 === 'Algeria';
            const algeriaGoals = algeriaHome ? parts[0] : parts[1];
            const otherGoals = algeriaHome ? parts[1] : parts[0];
            cls = algeriaGoals > otherGoals ? 'win' : (algeriaGoals < otherGoals ? 'loss' : 'draw');
        }
    }
    return `
        <tr class="${cls}">
            <td>${m.date || 'TBD'}</td>
            <td>${m.competition || '-'}</td>
            <td>${m.team1} <strong>${m.score}</strong> ${m.team2}</td>
            <td>${m.venue || '-'}</td>
        </tr>
    `;
}

function isUpcoming(m) {
    return !m.score || m.score.trim().toLowerCase() === 'v';
}

function renderMatches(list) {
    const upcoming = list.filter(isUpcoming);
    const results = list.filter(m => !isUpcoming(m)).reverse();
    document.querySelector('#upcomingTable tbody').innerHTML = upcoming.map(matchRowHTML).join('') || '<tr><td colspan="4">Aucun match à venir trouvé</td></tr>';
    document.querySelector('#resultsTable tbody').innerHTML = results.map(matchRowHTML).join('') || '<tr><td colspan="4">Aucun résultat trouvé</td></tr>';
}
renderMatches(DATA.matches);

document.getElementById('matchSearch').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    renderMatches(DATA.matches.filter(m =>
        (m.competition||'').toLowerCase().includes(q) ||
        (m.team1||'').toLowerCase().includes(q) ||
        (m.team2||'').toLowerCase().includes(q)
    ));
});

const appearances = DATA.records.filter(r => r.type === 'appearances');
const goals = DATA.records.filter(r => r.type === 'goals');

document.querySelector('#appearancesTable tbody').innerHTML = appearances.map(r => `
    <tr><td>${r.rank}</td><td>${r.player}</td><td class="value">${r.value}</td><td>${r.career}</td></tr>
`).join('');

document.querySelector('#goalsTable tbody').innerHTML = goals.map(r => `
    <tr><td>${r.rank}</td><td>${r.player}</td><td class="value">${r.value}</td><td>${r.career}</td></tr>
`).join('');

function compRowHTML(c) {
    return `
        <tr>
            <td>${c.year || '-'}</td>
            <td>${c.round || '-'}</td>
            <td>${c.position || '-'}</td>
            <td>${c.played || '-'}</td>
            <td>${c.wins || '-'}</td>
            <td>${c.draws || '-'}</td>
            <td>${c.losses || '-'}</td>
            <td>${c.gf || '-'}</td>
            <td>${c.ga || '-'}</td>
        </tr>
    `;
}

const worldCup = DATA.competitions.filter(c => c.competition === 'FIFA World Cup');
const afcon = DATA.competitions.filter(c => c.competition === 'Africa Cup of Nations');

document.querySelector('#worldCupTable tbody').innerHTML = worldCup.map(compRowHTML).join('') || '<tr><td colspan="9">Aucune donnée</td></tr>';
document.querySelector('#afconTable tbody').innerHTML = afcon.map(compRowHTML).join('') || '<tr><td colspan="9">Aucune donnée</td></tr>';

document.querySelector('#fifaCards').innerHTML = DATA.fifa_cards.map(c => `
    <div class="fifa-card-wrapper">
        <div class="fifa-card">
            ${c.bg ? `<img class="bg" src="${c.bg}" alt="">` : ''}
            <span class="rating-text">${c.rating}</span>
            <span class="pos-text">${c.position}</span>
            ${c.image ? `<img class="photo" src="${c.image}" alt="${c.name}">` : ''}
        </div>
        <div class="fifa-card-name">${c.name}</div>
        <div class="fifa-badges">
            ${c.nation_flag ? `<img src="${c.nation_flag}" alt="Nation">` : ''}
            ${c.club_logo ? `<img src="${c.club_logo}" alt="Club">` : ''}
        </div>
        <div class="fifa-stats-grid">
            <div>PAC <b>${c.pac}</b></div><div>SHO <b>${c.sho}</b></div>
            <div>PAS <b>${c.pas}</b></div><div>DRI <b>${c.dri}</b></div>
            <div>DEF <b>${c.de}</b></div><div>PHY <b>${c.phy}</b></div>
        </div>
    </div>
`).join('');

let sortDir = {};
document.querySelectorAll('#playersTable th').forEach(th => {
    th.addEventListener('click', () => {
        const key = th.dataset.key;
        sortDir[key] = !sortDir[key];
        const sorted = [...DATA.players].sort((a, b) => {
            let va = a[key], vb = b[key];
            if (typeof va === 'string') return sortDir[key] ? va.localeCompare(vb) : vb.localeCompare(va);
            return sortDir[key] ? (va||0) - (vb||0) : (vb||0) - (va||0);
        });
        renderPlayers(sorted);
    });
});
</script>

</body>
</html>
"""

html_output = html_template.replace("__DATA_JSON__", data_json)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_output)

print(f"Site généré avec succès : {OUTPUT_PATH}")
print(f"{len(players)} joueurs, {len(matches)} matchs, {len(records)} records, {len(competitions)} lignes compétitions, {len(fifa_cards)} cartes FIFA")