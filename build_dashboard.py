#!/usr/bin/env python3
"""
scripts/build_dashboard.py
Reads dist/metrics.json and generates dist/index.html
"""

import json
from datetime import datetime
from pathlib import Path

DIST = Path("dist")
metrics_path = DIST / "metrics.json"

if not metrics_path.exists():
    print("metrics.json not found — run collect_metrics.py first")
    exit(1)

data = json.loads(metrics_path.read_text())
summary = data["summary"]
repos = data["repos"]


def score_class(score):
    if score >= 80:
        return "score-high"
    if score >= 60:
        return "score-mid"
    return "score-low"


def score_label(score):
    if score >= 80:
        return "Healthy"
    if score >= 60:
        return "Fair"
    return "Needs attention"


def staleness_class(s):
    return {
        "fresh": "fresh",
        "recent": "recent",
        "aging": "aging",
        "stale": "stale",
        "dormant": "dormant",
    }.get(s, "")


def lang_color(lang):
    colors = {
        "Python": "#3572A5",
        "JavaScript": "#f1e05a",
        "TypeScript": "#2b7489",
        "Shell": "#89e051",
        "Go": "#00ADD8",
        "Rust": "#dea584",
        "Ruby": "#701516",
        "Java": "#b07219",
        "C++": "#f34b7d",
        "C": "#555555",
        "HTML": "#e34c26",
    }
    return colors.get(lang, "#666")


def fmt_date(iso):
    if not iso:
        return "never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return iso[:10]


def repo_cards_html():
    html = ""
    for r in repos:
        sc = score_class(r["health_score"])
        sl = staleness_class(r["staleness"])
        stale_html = ""
        if r["stale_branch_count"]:
            stale_html = f'<span class="badge badge-warn">⚠ {r["stale_branch_count"]} stale branch{"es" if r["stale_branch_count"] > 1 else ""}</span>'
        pr_html = ""
        if r["open_pr_count"]:
            pr_html = f'<span class="badge badge-info">⇄ {r["open_pr_count"]} open PR{"s" if r["open_pr_count"] > 1 else ""}</span>'
        issue_html = ""
        if r["open_issues_count"]:
            issue_html = f'<span class="badge badge-neutral">◎ {r["open_issues_count"]} issue{"s" if r["open_issues_count"] > 1 else ""}</span>'
        dep_html = ""
        if r["dependabot_alerts"]:
            dep_html = f'<span class="badge badge-danger">⚡ {r["dependabot_alerts"]} dependabot</span>'

        protection_icon = "🔒" if r["branch_protection"] else "🔓"
        license_icon = "📄" if r["has_license"] else "⚠️"
        lang_dot = (
            f'<span class="lang-dot" style="background:{lang_color(r["language"])}"></span>{r["language"]}'
            if r["language"]
            else ""
        )

        topics_html = "".join(
            f'<span class="topic">{t}</span>' for t in r.get("topics", [])[:4]
        )

        html += f"""
        <div class="repo-card {sc}">
          <div class="card-header">
            <div class="card-title-row">
              <a href="{r["url"]}" target="_blank" class="repo-name">{r["name"]}</a>
              <div class="score-badge {sc}">{r["health_score"]}</div>
            </div>
            <div class="card-meta">
              {lang_dot}
              <span class="staleness-pill {sl}">{r["staleness"]}</span>
              <span class="commit-date">Last commit: {fmt_date(r["last_commit_date"])}</span>
            </div>
            {f'<p class="repo-desc">{r["description"]}</p>' if r["description"] else ""}
            <div class="topics">{topics_html}</div>
          </div>
          <div class="card-badges">
            {stale_html}{pr_html}{issue_html}{dep_html}
          </div>
          <div class="card-footer">
            <span title="Branch protection">{protection_icon} Branch protection</span>
            <span title="License">{license_icon} {r["license"] or "No license"}</span>
            <span title="Default branch">⎇ {r["default_branch"]}</span>
          </div>
        </div>"""
    return html


generated_at = fmt_date(summary["generated_at"])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Repo Health — {summary["username"]}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:        #0d0f14;
    --surface:   #13161e;
    --surface2:  #1c2030;
    --border:    #252a38;
    --text:      #c9d1e0;
    --text-dim:  #6b7694;
    --green:     #3dd68c;
    --yellow:    #f0c040;
    --orange:    #f07840;
    --red:       #e05070;
    --blue:      #5090e8;
    --purple:    #9070e0;
    --mono:      'IBM Plex Mono', monospace;
    --sans:      'IBM Plex Sans', sans-serif;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* ── Header ── */
  header {{
    border-bottom: 1px solid var(--border);
    padding: 32px 40px 24px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .header-left h1 {{
    font-family: var(--mono);
    font-size: 22px;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.02em;
  }}
  .header-left h1 span {{ color: var(--green); }}
  .header-left .subtitle {{
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 4px;
  }}
  .generated {{
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
  }}
  .header-right {{
    display: flex;
    align-items: flex-end;
    gap: 16px;
  }}
  .logout-btn {{
    font-family: var(--mono);
    font-size: 11px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    text-decoration: none;
  }}
  .logout-btn:hover {{
    border-color: var(--red);
    color: var(--red);
  }}

  /* ── Summary bar ── */
  .summary-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1px;
    background: var(--border);
    border-bottom: 1px solid var(--border);
  }}
  .stat {{
    background: var(--surface);
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .stat-value {{
    font-family: var(--mono);
    font-size: 28px;
    font-weight: 600;
    color: #fff;
    line-height: 1;
  }}
  .stat-value.green  {{ color: var(--green); }}
  .stat-value.yellow {{ color: var(--yellow); }}
  .stat-value.orange {{ color: var(--orange); }}
  .stat-value.red    {{ color: var(--red); }}
  .stat-label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    font-family: var(--mono);
  }}

  /* ── Controls ── */
  .controls {{
    padding: 16px 40px;
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
  }}
  .filter-btn {{
    font-family: var(--mono);
    font-size: 11px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .filter-btn:hover, .filter-btn.active {{
    background: var(--surface);
    border-color: var(--green);
    color: var(--green);
  }}
  .search {{
    font-family: var(--mono);
    font-size: 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 6px 12px;
    border-radius: 4px;
    outline: none;
    width: 200px;
    transition: border-color 0.15s;
  }}
  .search:focus {{ border-color: var(--blue); }}
  .search::placeholder {{ color: var(--text-dim); }}

  /* ── Grid ── */
  main {{
    padding: 24px 40px 48px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }}

  /* ── Cards ── */
  .repo-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    transition: border-color 0.15s, transform 0.1s;
    position: relative;
    overflow: hidden;
  }}
  .repo-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--border);
  }}
  .repo-card.score-high::before  {{ background: var(--green); }}
  .repo-card.score-mid::before   {{ background: var(--yellow); }}
  .repo-card.score-low::before   {{ background: var(--red); }}
  .repo-card:hover {{
    border-color: #3a4055;
    transform: translateY(-1px);
  }}

  .card-title-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }}
  .repo-name {{
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 600;
    color: #fff;
    text-decoration: none;
  }}
  .repo-name:hover {{ color: var(--blue); }}

  .score-badge {{
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 600;
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}
  .score-badge.score-high  {{ background: rgba(61,214,140,0.15); color: var(--green); }}
  .score-badge.score-mid   {{ background: rgba(240,192,64,0.15);  color: var(--yellow); }}
  .score-badge.score-low   {{ background: rgba(224,80,112,0.15);  color: var(--red); }}

  .card-meta {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 4px;
  }}
  .lang-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 4px;
    vertical-align: middle;
  }}
  .staleness-pill {{
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 3px;
  }}
  .fresh   {{ background: rgba(61,214,140,0.15); color: var(--green); }}
  .recent  {{ background: rgba(80,144,232,0.15); color: var(--blue); }}
  .aging   {{ background: rgba(240,192,64,0.15);  color: var(--yellow); }}
  .stale   {{ background: rgba(240,120,64,0.15);  color: var(--orange); }}
  .dormant {{ background: rgba(107,118,148,0.15); color: var(--text-dim); }}

  .commit-date {{ font-size: 11px; color: var(--text-dim); font-family: var(--mono); }}

  .repo-desc {{
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 4px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }}

  .topics {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  .topic {{
    font-family: var(--mono);
    font-size: 10px;
    background: rgba(144,112,224,0.15);
    color: var(--purple);
    padding: 2px 8px;
    border-radius: 3px;
    text-transform: lowercase;
  }}

  /* Badges */
  .card-badges {{ display: flex; gap: 6px; flex-wrap: wrap; min-height: 24px; }}
  .badge {{
    font-family: var(--mono);
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 4px;
  }}
  .badge-warn    {{ background: rgba(240,192,64,0.15);  color: var(--yellow); }}
  .badge-info    {{ background: rgba(80,144,232,0.15);  color: var(--blue); }}
  .badge-neutral {{ background: rgba(107,118,148,0.15); color: var(--text-dim); }}
  .badge-danger  {{ background: rgba(224,80,112,0.15);  color: var(--red); }}

  /* Card footer */
  .card-footer {{
    display: flex;
    gap: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    font-size: 11px;
    color: var(--text-dim);
    font-family: var(--mono);
    flex-wrap: wrap;
  }}

  /* Empty state */
  .empty {{ text-align: center; color: var(--text-dim); padding: 60px; font-family: var(--mono); }}

  /* Responsive */
  @media (max-width: 600px) {{
    header, .controls, main {{ padding-left: 16px; padding-right: 16px; }}
    .grid {{ grid-template-columns: 1fr; }}
  }}

  /* Animate cards in */
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  .repo-card {{ animation: fadeUp 0.25s ease both; }}
  .repo-card:nth-child(1)  {{ animation-delay: 0.03s; }}
  .repo-card:nth-child(2)  {{ animation-delay: 0.06s; }}
  .repo-card:nth-child(3)  {{ animation-delay: 0.09s; }}
  .repo-card:nth-child(4)  {{ animation-delay: 0.12s; }}
  .repo-card:nth-child(5)  {{ animation-delay: 0.15s; }}
  .repo-card:nth-child(6)  {{ animation-delay: 0.18s; }}
  .repo-card:nth-child(n+7) {{ animation-delay: 0.2s; }}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>⬡ repo health / <span>{summary["username"]}</span></h1>
    <div class="subtitle">automated hygiene dashboard · updated daily</div>
  </div>
  <div class="header-right">
    <div class="generated">Generated {generated_at}</div>
    <a href="/_signout" class="logout-btn">Logout</a>
  </div>
</header>

<div class="summary-bar">
  <div class="stat">
    <div class="stat-value {"green" if summary["avg_health_score"] >= 80 else "yellow" if summary["avg_health_score"] >= 60 else "red"}">{summary["avg_health_score"]}</div>
    <div class="stat-label">Avg Health Score</div>
  </div>
  <div class="stat">
    <div class="stat-value">{summary["total_repos"]}</div>
    <div class="stat-label">Active Repos</div>
  </div>
  <div class="stat">
    <div class="stat-value {"red" if summary["total_open_prs"] > 5 else "yellow" if summary["total_open_prs"] > 0 else "green"}">{summary["total_open_prs"]}</div>
    <div class="stat-label">Open PRs</div>
  </div>
  <div class="stat">
    <div class="stat-value {"orange" if summary["total_stale_branches"] > 0 else "green"}">{summary["total_stale_branches"]}</div>
    <div class="stat-label">Stale Branches</div>
  </div>
  <div class="stat">
    <div class="stat-value {"red" if summary["total_dependabot_alerts"] > 0 else "green"}">{summary["total_dependabot_alerts"]}</div>
    <div class="stat-label">Dependabot Alerts</div>
  </div>
  <div class="stat">
    <div class="stat-value {"green" if summary["repos_with_protection"] == summary["total_repos"] else "yellow"}">{summary["repos_with_protection"]}/{summary["total_repos"]}</div>
    <div class="stat-label">Branch Protected</div>
  </div>
</div>

<div class="controls">
  <input class="search" type="text" placeholder="Search repos..." id="search" oninput="filterCards()">
  <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
  <button class="filter-btn" onclick="setFilter('score-low', this)">⚠ Needs Attention</button>
  <button class="filter-btn" onclick="setFilter('score-mid', this)">◑ Fair</button>
  <button class="filter-btn" onclick="setFilter('score-high', this)">✓ Healthy</button>
  <button class="filter-btn" onclick="setFilter('stale', this)">⏱ Stale</button>
</div>

<main>
  <div class="grid" id="grid">
    {repo_cards_html()}
  </div>
  <div class="empty" id="empty" style="display:none">No repos match this filter.</div>
</main>

<script>
  let currentFilter = 'all';
  let searchTerm = '';

  function setFilter(f, btn) {{
    currentFilter = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterCards();
  }}

  function filterCards() {{
    searchTerm = document.getElementById('search').value.toLowerCase();
    const cards = document.querySelectorAll('.repo-card');
    let visible = 0;

    cards.forEach(card => {{
      const name = card.querySelector('.repo-name').textContent.toLowerCase();
      const desc = card.querySelector('.repo-desc')?.textContent.toLowerCase() || '';
      const matchesSearch = !searchTerm || name.includes(searchTerm) || desc.includes(searchTerm);
      const staleness = card.querySelector('.staleness-pill')?.textContent || '';

      let matchesFilter = currentFilter === 'all';
      if (currentFilter === 'stale') matchesFilter = ['stale','dormant','aging'].includes(staleness);
      else if (currentFilter !== 'all') matchesFilter = card.classList.contains(currentFilter);

      const show = matchesSearch && matchesFilter;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    }});

    document.getElementById('empty').style.display = visible === 0 ? '' : 'none';
  }}
</script>
</body>
</html>"""

(DIST / "index.html").write_text(html)
print(f"Dashboard written to dist/index.html ({len(html):,} bytes)")
