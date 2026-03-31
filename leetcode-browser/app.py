#!/usr/bin/env python3
"""
app.py - Local LeetCode Interview Question Browser
Usage: python app.py [--port 8000] [--host 127.0.0.1] [--db-path ./leetcode.db]
Then open: http://localhost:8000
"""

import argparse
import json
import os
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

DB_PATH = os.path.join(os.path.dirname(__file__), "leetcode.db")

# ---------------------------------------------------------------------------
# HTML / CSS / JS  (embedded as a string so app.py is fully self-contained)
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeetCode Interview Browser</title>
<style>
  :root {
    --bg: #0f0f0f;
    --surface: #1a1a1a;
    --surface2: #242424;
    --border: #2e2e2e;
    --text: #e8e8e8;
    --text-muted: #888;
    --accent: #f5a623;
    --easy: #00b8a3;
    --medium: #ffa116;
    --hard: #ff375f;
    --link: #6bb3f8;
    --radius: 6px;
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font); font-size: 14px; min-height: 100vh; }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  header h1 { font-size: 18px; font-weight: 700; color: var(--accent); letter-spacing: -0.3px; }
  header h1 span { color: var(--text-muted); font-weight: 400; font-size: 13px; margin-left: 10px; }

  /* ── Filters ── */
  .filters {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .filter-group { display: flex; align-items: center; gap: 6px; }
  .filter-group label { color: var(--text-muted); font-size: 12px; white-space: nowrap; }
  select, input[type="text"] {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 6px 10px;
    font-size: 13px;
    outline: none;
    transition: border-color .15s;
  }
  select:focus, input[type="text"]:focus { border-color: var(--accent); }
  select { cursor: pointer; }
  #company-input { width: 200px; }
  #search-input  { width: 200px; }

  .btn {
    background: var(--surface2);
    color: var(--text-muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 6px 14px;
    font-size: 13px;
    cursor: pointer;
    transition: background .15s, color .15s;
  }
  .btn:hover { background: var(--border); color: var(--text); }
  .btn-accent { background: var(--accent); color: #000; border-color: var(--accent); font-weight: 600; }
  .btn-accent:hover { background: #e0951f; }

  /* ── Toolbar (results count + pagination) ── */
  .toolbar {
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--text-muted);
    font-size: 13px;
    border-bottom: 1px solid var(--border);
  }
  .pagination { display: flex; gap: 4px; align-items: center; }
  .page-btn {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 4px;
    padding: 4px 10px;
    cursor: pointer;
    font-size: 13px;
    transition: background .15s;
  }
  .page-btn:hover:not(:disabled) { background: var(--border); }
  .page-btn:disabled { opacity: 0.3; cursor: default; }
  .page-btn.active { background: var(--accent); color: #000; border-color: var(--accent); font-weight: 700; }

  /* ── Table ── */
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; }
  thead { background: var(--surface); }
  th {
    padding: 10px 14px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .6px;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    user-select: none;
    position: sticky;
    top: 0;
    background: var(--surface);
    z-index: 50;
  }
  th.sortable { cursor: pointer; }
  th.sortable:hover { color: var(--text); }
  th .sort-icon { margin-left: 4px; opacity: 0.4; font-style: normal; }
  th.sort-asc .sort-icon,
  th.sort-desc .sort-icon { opacity: 1; color: var(--accent); }
  td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
  tr:hover td { background: var(--surface2); }

  /* ── Difficulty badges ── */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .4px;
  }
  .badge-EASY   { background: rgba(0,184,163,.15); color: var(--easy); }
  .badge-MEDIUM { background: rgba(255,161,22,.15); color: var(--medium); }
  .badge-HARD   { background: rgba(255,55,95,.15);  color: var(--hard); }

  /* ── Title link ── */
  .title-link { color: var(--text); text-decoration: none; font-weight: 500; }
  .title-link:hover { color: var(--link); text-decoration: underline; }
  .ext-icon { font-size: 10px; color: var(--text-muted); margin-left: 4px; }

  /* ── Frequency bar ── */
  .freq-cell { min-width: 100px; }
  .freq-bar-wrap { display: flex; align-items: center; gap: 8px; }
  .freq-bar-bg {
    flex: 1;
    height: 6px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
  }
  .freq-bar-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #f5a623, #ff6b6b);
  }
  .freq-val { font-size: 12px; color: var(--text-muted); min-width: 32px; text-align: right; }

  /* ── Acceptance ── */
  .accept-val { font-size: 13px; }
  .accept-high   { color: var(--easy); }
  .accept-medium { color: var(--medium); }
  .accept-low    { color: var(--hard); }

  /* ── Topic chips ── */
  .topics-cell { max-width: 260px; }
  .chip {
    display: inline-block;
    padding: 2px 8px;
    margin: 2px 2px 2px 0;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 11px;
    color: var(--text-muted);
    cursor: pointer;
    transition: background .12s, color .12s;
    white-space: nowrap;
  }
  .chip:hover { background: var(--border); color: var(--text); }
  .chip.active { background: rgba(245,166,35,.15); border-color: var(--accent); color: var(--accent); }

  /* ── Empty / loading states ── */
  .state-msg {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
    font-size: 15px;
  }
  .spinner {
    display: inline-block;
    width: 24px; height: 24px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .7s linear infinite;
    margin-bottom: 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Responsive ── */
  @media (max-width: 768px) {
    .filters { padding: 10px 12px; }
    th, td { padding: 8px 10px; }
    .topics-cell { display: none; }
    #company-input, #search-input { width: 150px; }
  }
</style>
</head>
<body>

<header>
  <h1>LeetCode Interview Browser <span id="company-count"></span></h1>
  <div style="display:flex;gap:8px;align-items:center">
    <span id="loading-indicator" style="display:none">
      <span class="spinner" style="width:16px;height:16px;border-width:2px"></span>
    </span>
  </div>
</header>

<div class="filters">
  <div class="filter-group">
    <label>Company</label>
    <input type="text" id="company-input" list="company-list" placeholder="All companies..." autocomplete="off">
    <datalist id="company-list"></datalist>
  </div>

  <div class="filter-group">
    <label>Period</label>
    <select id="period-select">
      <option value="">All periods</option>
      <option value="all" selected>All time</option>
      <option value="thirty_days">30 days</option>
      <option value="three_months">3 months</option>
      <option value="six_months">6 months</option>
      <option value="more_than_six">6+ months</option>
    </select>
  </div>

  <div class="filter-group">
    <label>Difficulty</label>
    <select id="difficulty-select">
      <option value="">All</option>
      <option value="EASY">Easy</option>
      <option value="MEDIUM">Medium</option>
      <option value="HARD">Hard</option>
    </select>
  </div>

  <div class="filter-group">
    <label>Topic</label>
    <select id="topic-select">
      <option value="">All topics</option>
    </select>
  </div>

  <div class="filter-group">
    <input type="text" id="search-input" placeholder="Search title...">
  </div>

  <button class="btn" onclick="clearFilters()">Clear</button>
</div>

<div class="toolbar">
  <div id="results-info">Loading...</div>
  <div class="pagination" id="pagination"></div>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th style="width:90px">Difficulty</th>
        <th class="sortable" data-sort="title" onclick="toggleSort('title')">
          Title <i class="sort-icon" id="sort-icon-title">↕</i>
        </th>
        <th class="sortable freq-cell" data-sort="frequency" onclick="toggleSort('frequency')">
          Frequency <i class="sort-icon" id="sort-icon-frequency">↕</i>
        </th>
        <th class="sortable" data-sort="acceptance" onclick="toggleSort('acceptance')">
          Accept % <i class="sort-icon" id="sort-icon-acceptance">↕</i>
        </th>
        <th class="topics-cell">Topics</th>
      </tr>
    </thead>
    <tbody id="results-body">
      <tr><td colspan="5" class="state-msg">
        <div class="spinner"></div><br>Loading...
      </td></tr>
    </tbody>
  </table>
</div>

<script>
// ── State ────────────────────────────────────────────────────────────────
const state = {
  company: '',
  period: 'all',
  difficulty: '',
  topic: '',
  search: '',
  sort: 'frequency',
  order: 'desc',
  page: 1,
  limit: 50,
  total: 0,
};

let searchTimer = null;
let currentTopicFilter = '';

// ── Boot ─────────────────────────────────────────────────────────────────
async function boot() {
  const [companies, topics] = await Promise.all([
    fetch('/api/companies').then(r => r.json()),
    fetch('/api/topics').then(r => r.json()),
  ]);

  // Populate company datalist
  const dl = document.getElementById('company-list');
  companies.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    dl.appendChild(opt);
  });
  document.getElementById('company-count').textContent =
    `— ${companies.length} companies`;

  // Populate topic dropdown
  const ts = document.getElementById('topic-select');
  topics.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    ts.appendChild(opt);
  });

  // Wire events
  document.getElementById('company-input').addEventListener('input', () => {
    state.company = document.getElementById('company-input').value.trim();
    state.page = 1;
    fetchProblems();
  });
  document.getElementById('period-select').addEventListener('change', () => {
    state.period = document.getElementById('period-select').value;
    state.page = 1;
    fetchProblems();
  });
  document.getElementById('difficulty-select').addEventListener('change', () => {
    state.difficulty = document.getElementById('difficulty-select').value;
    state.page = 1;
    fetchProblems();
  });
  document.getElementById('topic-select').addEventListener('change', () => {
    state.topic = document.getElementById('topic-select').value;
    currentTopicFilter = state.topic;
    state.page = 1;
    fetchProblems();
  });
  document.getElementById('search-input').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.search = document.getElementById('search-input').value.trim();
      state.page = 1;
      fetchProblems();
    }, 300);
  });

  // Keyboard shortcut: / focuses search
  document.addEventListener('keydown', e => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      document.getElementById('search-input').focus();
    }
  });

  fetchProblems();
}

// ── Fetch & Render ────────────────────────────────────────────────────────
async function fetchProblems() {
  setLoading(true);

  const params = new URLSearchParams();
  if (state.company)    params.set('company',    state.company);
  if (state.period)     params.set('period',     state.period);
  if (state.difficulty) params.set('difficulty', state.difficulty);
  if (state.topic)      params.set('topic',      state.topic);
  if (state.search)     params.set('search',     state.search);
  params.set('sort',  state.sort);
  params.set('order', state.order);
  params.set('page',  state.page);
  params.set('limit', state.limit);

  try {
    const data = await fetch('/api/problems?' + params).then(r => r.json());
    state.total = data.total;
    renderTable(data.results);
    renderToolbar(data.total, data.page, data.limit);
  } catch(e) {
    document.getElementById('results-body').innerHTML =
      `<tr><td colspan="5" class="state-msg">Error loading data. Is the server running?</td></tr>`;
  }

  setLoading(false);
}

function renderTable(rows) {
  const tbody = document.getElementById('results-body');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="state-msg">No problems found for these filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const diffClass = `badge-${r.difficulty}`;
    const acceptPct = (r.acceptance * 100).toFixed(1);
    const acceptClass = r.acceptance >= 0.5 ? 'accept-high'
                      : r.acceptance >= 0.35 ? 'accept-medium'
                      : 'accept-low';
    const freqPct = Math.round(r.frequency);
    const topics = r.topics
      ? r.topics.split(', ').map(t => {
          const active = t === currentTopicFilter ? ' active' : '';
          return `<span class="chip${active}" onclick="setTopic('${escHtml(t)}')">${escHtml(t)}</span>`;
        }).join('')
      : '';

    return `
      <tr>
        <td><span class="badge ${diffClass}">${cap(r.difficulty)}</span></td>
        <td>
          <a class="title-link" href="${escHtml(r.link)}" target="_blank" rel="noopener">
            ${escHtml(r.title)}<span class="ext-icon">↗</span>
          </a>
        </td>
        <td class="freq-cell">
          <div class="freq-bar-wrap">
            <div class="freq-bar-bg">
              <div class="freq-bar-fill" style="width:${freqPct}%"></div>
            </div>
            <span class="freq-val">${freqPct}</span>
          </div>
        </td>
        <td><span class="accept-val ${acceptClass}">${acceptPct}%</span></td>
        <td class="topics-cell">${topics}</td>
      </tr>`;
  }).join('');
}

function renderToolbar(total, page, limit) {
  const from = total === 0 ? 0 : (page - 1) * limit + 1;
  const to   = Math.min(page * limit, total);
  const totalPages = Math.ceil(total / limit);

  document.getElementById('results-info').textContent =
    total === 0
      ? 'No results'
      : `Showing ${from}–${to} of ${total} problems`;

  // Pagination: prev, up to 7 page buttons, next
  let html = '';
  html += `<button class="page-btn" onclick="goPage(${page-1})" ${page<=1?'disabled':''}>‹</button>`;

  let pages = [];
  if (totalPages <= 7) {
    pages = Array.from({length: totalPages}, (_, i) => i + 1);
  } else {
    const left = Math.max(1, page - 2);
    const right = Math.min(totalPages, page + 2);
    if (left > 1)           { pages.push(1); if (left > 2) pages.push('...'); }
    for (let p = left; p <= right; p++) pages.push(p);
    if (right < totalPages) { if (right < totalPages-1) pages.push('...'); pages.push(totalPages); }
  }
  pages.forEach(p => {
    if (p === '...') {
      html += `<span style="color:var(--text-muted);padding:0 4px">…</span>`;
    } else {
      html += `<button class="page-btn${p===page?' active':''}" onclick="goPage(${p})">${p}</button>`;
    }
  });

  html += `<button class="page-btn" onclick="goPage(${page+1})" ${page>=totalPages?'disabled':''}>›</button>`;
  document.getElementById('pagination').innerHTML = html;
}

// ── Actions ───────────────────────────────────────────────────────────────
function goPage(p) {
  const totalPages = Math.ceil(state.total / state.limit);
  if (p < 1 || p > totalPages) return;
  state.page = p;
  fetchProblems();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function toggleSort(col) {
  if (state.sort === col) {
    state.order = state.order === 'desc' ? 'asc' : 'desc';
  } else {
    state.sort = col;
    state.order = col === 'title' ? 'asc' : 'desc';
  }
  state.page = 1;
  updateSortIcons();
  fetchProblems();
}

function updateSortIcons() {
  ['frequency', 'acceptance', 'title'].forEach(col => {
    const th = document.querySelector(`th[data-sort="${col}"]`);
    const icon = document.getElementById(`sort-icon-${col}`);
    if (!th || !icon) return;
    th.classList.remove('sort-asc', 'sort-desc');
    icon.textContent = '↕';
    if (state.sort === col) {
      th.classList.add(state.order === 'asc' ? 'sort-asc' : 'sort-desc');
      icon.textContent = state.order === 'asc' ? '↑' : '↓';
    }
  });
}

function setTopic(t) {
  if (currentTopicFilter === t) {
    // Deselect
    currentTopicFilter = '';
    state.topic = '';
    document.getElementById('topic-select').value = '';
  } else {
    currentTopicFilter = t;
    state.topic = t;
    document.getElementById('topic-select').value = t;
  }
  state.page = 1;
  fetchProblems();
}

function clearFilters() {
  state.company    = '';
  state.period     = 'all';
  state.difficulty = '';
  state.topic      = '';
  state.search     = '';
  state.sort       = 'frequency';
  state.order      = 'desc';
  state.page       = 1;
  currentTopicFilter = '';
  document.getElementById('company-input').value   = '';
  document.getElementById('period-select').value   = 'all';
  document.getElementById('difficulty-select').value = '';
  document.getElementById('topic-select').value    = '';
  document.getElementById('search-input').value    = '';
  updateSortIcons();
  fetchProblems();
}

function setLoading(on) {
  document.getElementById('loading-indicator').style.display = on ? 'inline-block' : 'none';
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function cap(s) {
  return s.charAt(0) + s.slice(1).toLowerCase();
}

// ── Init ──────────────────────────────────────────────────────────────────
updateSortIcons();
boot();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Suppress default Apache-style logging; show a cleaner version
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path
        qs     = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)

        def qget(key, default=""):
            v = qs.get(key, [default])
            return v[0] if v else default

        if path == "/":
            self.send_html(HTML)

        elif path == "/api/companies":
            conn = get_db()
            rows = conn.execute("SELECT name FROM companies ORDER BY name COLLATE NOCASE").fetchall()
            conn.close()
            self.send_json([r["name"] for r in rows])

        elif path == "/api/topics":
            conn = get_db()
            rows = conn.execute("SELECT name FROM topics ORDER BY name COLLATE NOCASE").fetchall()
            conn.close()
            self.send_json([r["name"] for r in rows])

        elif path == "/api/problems":
            self._handle_problems(qget)

        else:
            self.send_response(404)
            self.end_headers()

    def _handle_problems(self, qget):
        company    = qget("company")
        period     = qget("period")
        difficulty = qget("difficulty")
        topic      = qget("topic")
        search     = qget("search")
        sort       = qget("sort", "frequency")
        order      = qget("order", "desc")
        try:
            page  = max(1, int(qget("page",  "1")))
            limit = min(200, max(1, int(qget("limit", "50"))))
        except ValueError:
            page, limit = 1, 50

        # Validate sort / order to prevent SQL injection
        sort_col_map = {
            "frequency":  "a.frequency",
            "acceptance": "p.acceptance",
            "difficulty": "CASE p.difficulty WHEN 'EASY' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END",
            "title":      "p.title",
        }
        order_sql = "DESC" if order.lower() != "asc" else "ASC"
        sort_expr = sort_col_map.get(sort, "a.frequency")

        # Dynamic WHERE building
        wheres = []
        params = []

        if company:
            wheres.append("c.name = ?")
            params.append(company)
        if period:
            wheres.append("a.period = ?")
            params.append(period)
        if difficulty:
            wheres.append("p.difficulty = ?")
            params.append(difficulty.upper())
        if search:
            wheres.append("p.title LIKE ?")
            params.append(f"%{search}%")
        if topic:
            wheres.append(
                "EXISTS (SELECT 1 FROM problem_topics pt2"
                "        JOIN topics t2 ON t2.id = pt2.topic_id"
                "        WHERE pt2.slug = p.slug AND t2.name = ?)"
            )
            params.append(topic)

        where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""

        base_query = f"""
            SELECT
                p.slug,
                p.title,
                p.difficulty,
                p.link,
                p.acceptance,
                a.frequency,
                (SELECT GROUP_CONCAT(t.name, ', ')
                 FROM problem_topics pt
                 JOIN topics t ON t.id = pt.topic_id
                 WHERE pt.slug = p.slug
                 ORDER BY t.name) AS topics
            FROM appearances a
            JOIN problems  p ON p.slug   = a.problem_slug
            JOIN companies c ON c.id     = a.company_id
            {where_sql}
            ORDER BY {sort_expr} {order_sql}
        """

        count_query = f"""
            SELECT COUNT(*) AS cnt
            FROM appearances a
            JOIN problems  p ON p.slug = a.problem_slug
            JOIN companies c ON c.id   = a.company_id
            {where_sql}
        """

        offset = (page - 1) * limit
        paged_query = base_query + f"\nLIMIT {limit} OFFSET {offset}"

        conn = get_db()
        total  = conn.execute(count_query, params).fetchone()["cnt"]
        rows   = conn.execute(paged_query,  params).fetchall()
        conn.close()

        results = [
            {
                "slug":       r["slug"],
                "title":      r["title"],
                "difficulty": r["difficulty"],
                "link":       r["link"],
                "acceptance": r["acceptance"],
                "frequency":  r["frequency"],
                "topics":     r["topics"] or "",
            }
            for r in rows
        ]

        self.send_json({"total": total, "page": page, "limit": limit, "results": results})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global DB_PATH

    parser = argparse.ArgumentParser(description="LeetCode Interview Question Browser")
    parser.add_argument("--port",    type=int, default=8000)
    parser.add_argument("--host",    default="127.0.0.1",
                        help="Host to bind to (use 0.0.0.0 to expose to the network / containers)")
    parser.add_argument("--db-path", default=DB_PATH)
    args = parser.parse_args()

    DB_PATH = args.db_path

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run 'python import_data.py' first to build the database.")
        raise SystemExit(1)

    server = HTTPServer((args.host, args.port), Handler)
    display_host = "localhost" if args.host in ("0.0.0.0", "") else args.host
    url = f"http://{display_host}:{args.port}"
    print(f"LeetCode Browser running at  {url}")
    print("Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
