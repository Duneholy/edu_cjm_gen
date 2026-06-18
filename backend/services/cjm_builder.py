# -*- coding: utf-8 -*-
"""Генерация HTML-просмотрщика CJM из JSON."""
from __future__ import annotations

import json
import re
from typing import Any

from .cjm_rows import DEFAULT_ROWS, enrich_rows


def mod_key(name: str) -> str:
    return re.sub(r"\s*\(продолжение\)", "", name or "", flags=re.I).strip()[:40]


def module_color(name: str) -> str:
    n = (name or "").lower()
    if "этап 4" in n or "завершение" in n or "питч" in n:
        return "#2d6a4f"
    if "этап 3" in n or "mvp" in n:
        return "#b45309"
    if "этап 2" in n or "бизнес-гипотез" in n or "идея" in n:
        return "#6d28d9"
    if "этап 1" in n or "рынк" in n:
        return "#0369a1"
    if "этап 0" in n or "знакомство" in n:
        return "#0e7490"
    if "сбор" in n or "входной" in n or "распредел" in n or "подготовк" in n:
        return "#64748b"
    return "#64748b"


def ensure_module_names(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Группирует столбцы по module и подставляет «Этап N», если имя не задано."""
    if not stages:
        return stages

    result: list[dict[str, Any]] = []
    last_key: str | None = None
    group_num = 0
    group_name = ""

    for stage in stages:
        raw_mod = (stage.get("module") or "").strip()
        key = mod_key(raw_mod)
        if key != last_key:
            group_num += 1
            group_name = raw_mod or f"Этап {group_num}"
            last_key = key
        item = dict(stage)
        item["module"] = group_name
        result.append(item)
    return result


def build_module_groups(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    last_key: str | None = None
    current: dict[str, Any] | None = None

    for stage in stages:
        name = (stage.get("module") or "").strip()
        key = mod_key(name)
        if key != last_key:
            if current:
                groups.append(current)
            current = {
                "name": name,
                "span": 1,
                "color": stage.get("color") or module_color(name),
            }
            last_key = key
        elif current:
            current["span"] += 1
        else:
            current = {
                "name": name or "Этап 1",
                "span": 1,
                "color": stage.get("color") or module_color(name),
            }
            last_key = key

    if current:
        groups.append(current)
    return groups


def normalize_cjm(data: dict[str, Any], custom_rows: list[dict[str, str]] | None = None) -> dict[str, Any]:
    if custom_rows:
        rows = enrich_rows(custom_rows)
    else:
        rows = enrich_rows(
            [
                {"key": r["key"], "title": r.get("title", r["key"]), "sub": r.get("sub", "")}
                for r in (data.get("rows") or DEFAULT_ROWS)
            ]
        )
    raw_stages = ensure_module_names(list(data.get("stages", [])))
    stages = []
    for s in raw_stages:
        mod = s.get("module", "")
        stage = {
            "col": s.get("col", ""),
            "module": mod,
            "dateTime": s.get("dateTime", ""),
            "title": s.get("title", ""),
            "format": s.get("format", ""),
            "color": s.get("color") or module_color(mod),
        }
        for row in rows:
            val = s.get(row["key"], "—")
            stage[row["key"]] = val if val and str(val).strip() else "—"
        stages.append(stage)
    return {
        "programTitle": data.get("programTitle", "Customer Journey Map"),
        "programMeta": data.get("programMeta", ""),
        "rows": rows,
        "stages": stages,
        "moduleGroups": build_module_groups(stages),
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg: #f3f1ec; --surface: #ffffff; --surface2: #faf9f6;
      --border: rgba(0,0,0,0.08); --border-strong: rgba(0,0,0,0.12);
      --text: #1a1a1a; --muted: rgba(64,64,64,0.65);
      --accent: #d4ff00; --accent-dark: #b8e600;
      --col-hdr-a: #ffffff; --col-hdr-b: #dce8f4;
      --col-hdr-text-a: #1a5f7a; --col-hdr-text-b: #2d4a6f;
      --row-w: 220px; --col-w: 320px; --module-h: 40px; --header-h: 152px;
      --radius: 16px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Inter, "Segoe UI", system-ui, sans-serif;
      background: var(--bg); color: var(--text);
      height: 100vh; overflow: hidden;
      display: flex; flex-direction: column;
      -webkit-font-smoothing: antialiased;
    }
    .topbar {
      flex-shrink: 0; padding: 16px 24px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      display: flex; align-items: flex-start; justify-content: space-between;
      gap: 20px; flex-wrap: nowrap;
      width: 100%;
      max-width: 100vw;
    }
    .topbar-main { flex: 1 1 auto; min-width: 0; }
    .topbar-brand {
      font-size: 0.72rem; font-weight: 700;
      text-transform: lowercase; letter-spacing: 0.02em;
      color: var(--muted); margin-bottom: 6px;
    }
    .topbar h1 {
      font-size: 1.35rem; font-weight: 800;
      letter-spacing: -0.02em; line-height: 1.2;
      color: var(--text);
    }
    .topbar .meta {
      font-size: 0.84rem; color: var(--muted);
      max-width: 144ch; line-height: 1.5; margin-top: 6px;
    }
    .topbar-right {
      flex: 0 0 auto;
      display: flex; flex-direction: column; align-items: flex-end; gap: 10px;
      max-width: min(520px, 42vw);
    }
    .legend { display: flex; gap: 8px; flex-wrap: wrap; font-size: 0.72rem; justify-content: flex-end; }
    .legend span {
      display: inline-flex; align-items: center; gap: 6px;
      color: var(--muted); padding: 4px 10px;
      border-radius: 999px; background: var(--surface2);
      border: 1px solid var(--border);
    }
    .legend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .hint {
      font-size: 0.72rem; color: var(--muted);
      padding: 5px 12px; border-radius: 999px;
      background: var(--accent); color: var(--text); font-weight: 600;
    }
    .board-wrap { flex: 1; overflow: auto; background: var(--bg); padding: 16px; }
    .board {
      width: max-content;
      min-width: 100%;
    }
    .board-grid {
      display: grid; align-items: stretch;
      width: 100%;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.05);
      background: var(--surface);
    }
    .corner {
      position: sticky; top: 0; left: 0; z-index: 30;
      background: var(--surface2);
      border-right: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      padding: 14px;
      display: flex; flex-direction: column; justify-content: flex-end;
      font-size: 0.68rem; font-weight: 700;
      color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em;
    }
    .corner::before {
      content: "edu_cjm_gen";
      font-size: 0.62rem; font-weight: 800;
      text-transform: lowercase; letter-spacing: 0;
      margin-bottom: auto; padding-top: 4px; color: var(--text);
    }
    .row-label {
      position: sticky; left: 0; z-index: 15;
      padding: 14px 14px 14px 12px;
      border-right: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      border-left: 4px solid transparent;
      display: flex; flex-direction: column; justify-content: center;
      min-height: 120px;
    }
    .row-label strong { font-size: 0.82rem; font-weight: 700; display: block; line-height: 1.35; }
    .row-label small { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }
    .module-band {
      position: sticky; top: 0; z-index: 20;
      min-height: var(--module-h);
      padding: 8px 14px;
      border-bottom: 1px solid var(--border);
      border-right: 1px solid var(--border);
      display: flex; align-items: center;
      font-size: 0.72rem; font-weight: 700;
      letter-spacing: 0.03em; line-height: 1.25;
      background: var(--surface2);
      color: var(--text);
    }
    .module-band .band-label {
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .stage-header {
      position: sticky; top: var(--module-h); z-index: 10;
      height: var(--header-h);
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      border-right: 1px solid var(--border);
      display: flex; flex-direction: column;
    }
    .stage-header .mod {
      display: none;
    }
    .stage-header .date { font-size: 0.72rem; color: var(--muted); margin-bottom: 4px; }
    .stage-header h2 { font-size: 0.82rem; font-weight: 700; line-height: 1.35; flex: 1; }
    .stage-header .badge {
      display: inline-block; margin-top: 6px; padding: 3px 10px;
      font-size: 0.62rem; font-weight: 600; border-radius: 999px;
      background: rgba(255,255,255,0.55); color: var(--muted);
      border: 1px solid var(--border); max-width: 100%; line-height: 1.3;
    }
    .stage-header.col-a { background: var(--col-hdr-a); }
    .stage-header.col-b { background: var(--col-hdr-b); }
    .cell {
      padding: 14px;
      border-bottom: 1px solid var(--border);
      border-right: 1px solid var(--border);
      font-size: 0.78rem; line-height: 1.5;
      overflow-wrap: anywhere;
      min-height: 120px;
      display: flex; flex-direction: column;
    }
    .cell.empty { color: var(--muted); font-style: italic; }
    .cell .cell-inner { flex: 1; }
    .cell ul { margin: 6px 0 6px 1.1em; padding: 0; }
    .cell li { margin-bottom: 4px; }
    .cell table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 0.74rem; }
    .cell th, .cell td { border: 1px solid var(--border); padding: 5px 8px; text-align: left; vertical-align: top; }
    .cell th { background: var(--surface2); color: var(--muted); font-weight: 600; }
    .module-divider {
      position: sticky; top: 0; z-index: 5;
      background: var(--bg);
      border-right: 1px solid var(--border);
      writing-mode: vertical-rl; text-orientation: mixed;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.55rem; font-weight: 700; color: var(--muted);
      letter-spacing: 0.08em; text-transform: uppercase;
    }
    .scroll-hint {
      position: fixed; bottom: 16px; right: 20px;
      background: var(--text); color: #fff;
      padding: 8px 16px; border-radius: 999px;
      font-size: 0.72rem; font-weight: 600; z-index: 30;
    }
    .cjm-footer {
      flex-shrink: 0; padding: 10px 24px;
      text-align: center; font-size: 0.72rem;
      color: var(--muted); border-top: 1px solid var(--border);
      background: var(--surface);
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-main">
      <div class="topbar-brand">edu_cjm_gen · EdTech CJM</div>
      <h1>__TITLE__</h1>
      <p class="meta">__META__</p>
    </div>
    <div class="topbar-right">
      <div class="legend" id="legend"></div>
      <p class="hint">← прокрутите вправо →</p>
    </div>
  </header>
  <div class="board-wrap" id="boardWrap">
    <div class="board" id="board"></div>
  </div>
  <div class="scroll-hint">Shift + колёсико — горизонтальная прокрутка</div>
  <footer class="cjm-footer">edu_cjm_gen © Yury Mikhno, 2026</footer>
  <script>
    const STAGES = __STAGES__;
    const ROWS = __ROWS__;
    const MODULE_GROUPS = __MODULE_GROUPS__;
    const COL_HDR = [
      { bg: 'col-a', mod: 'var(--col-hdr-text-a)' },
      { bg: 'col-b', mod: 'var(--col-hdr-text-b)' },
    ];
    function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
    function rowTint(color, alpha) {
      const h = (color || '#94a3b8').replace('#', '');
      const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h.slice(0, 6);
      const r = parseInt(full.slice(0, 2), 16);
      const g = parseInt(full.slice(2, 4), 16);
      const b = parseInt(full.slice(4, 6), 16);
      return `rgba(${r},${g},${b},${alpha})`;
    }
    document.getElementById('legend').innerHTML = ROWS.map(r => {
      const short = r.title.length > 42 ? r.title.slice(0, 40) + '…' : r.title;
      return `<span><i style="background:${r.color}"></i>${esc(short)}</span>`;
    }).join('');
    function fmtInline(t) {
      return esc(t).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>');
    }
    function mdTableToHtml(lines) {
      const rows = lines.filter(l => l.trim().startsWith('|'));
      if (rows.length < 2) return lines.map(l => esc(l)).join('<br>');
      const parse = row => row.split('|').slice(1, -1).map(c => c.trim());
      const header = parse(rows[0]);
      const bodyRows = rows.slice(2).map(parse);
      let h = '<table><thead><tr>' + header.map(c => `<th>${fmtInline(c)}</th>`).join('') + '</tr></thead><tbody>';
      bodyRows.forEach(r => { h += '<tr>' + r.map(c => `<td>${fmtInline(c)}</td>`).join('') + '</tr>'; });
      return h + '</tbody></table>';
    }
    function fmt(t) {
      if (!t || t === '—') return '<span class="empty">—</span>';
      const blocks = t.split(/\n\n+/);
      return blocks.map(block => {
        const lines = block.split('\n');
        if (lines.some(l => l.trim().startsWith('|'))) return mdTableToHtml(lines);
        if (lines.every(l => /^[-*]\s/.test(l.trim()) || !l.trim())) {
          const items = lines.filter(l => l.trim()).map(l => `<li>${fmtInline(l.replace(/^[-*]\s+/, ''))}</li>`).join('');
          return `<ul>${items}</ul>`;
        }
        return lines.map(l => fmtInline(l)).join('<br>');
      }).join('<br><br>');
    }
    function moduleShort(name) {
      const m = (name || '').match(/этап\s*(\d)/i);
      if (m) return 'Э' + m[1];
      if (/сбор|входной|распредел|подготовк/i.test(name)) return 'Старт';
      return '·';
    }
    function modKey(name) {
      return (name || '').replace(/\s*\(продолжение\)/gi, '').trim().slice(0, 40);
    }
    const colTracks = ['var(--row-w)'];
    let lastModule = '';
    STAGES.forEach((s, i) => {
      const key = modKey(s.module);
      if (i > 0 && key !== lastModule) colTracks.push('28px');
      colTracks.push('var(--col-w)');
      lastModule = key;
    });
    const totalRows = ROWS.length + 2;
    const board = document.createElement('div');
    board.className = 'board-grid';
    board.style.gridTemplateColumns = colTracks.join(' ');
    board.style.gridTemplateRows = `var(--module-h) var(--header-h) repeat(${ROWS.length}, minmax(120px, auto))`;
    const corner = document.createElement('div');
    corner.className = 'corner';
    corner.textContent = 'CJM';
    corner.style.gridRow = '1 / span 2';
    corner.style.gridColumn = '1';
    board.appendChild(corner);

    let bandCol = 2;
    let groupIdx = 0;
    MODULE_GROUPS.forEach((group) => {
      if (groupIdx > 0) bandCol += 1;
      const band = document.createElement('div');
      band.className = 'module-band';
      band.style.gridRow = '1';
      band.style.gridColumn = `${bandCol} / span ${group.span}`;
      band.style.borderLeft = `4px solid ${group.color || '#64748b'}`;
      band.innerHTML = `<span class="band-label">${esc(group.name)}</span>`;
      board.appendChild(band);
      bandCol += group.span;
      groupIdx += 1;
    });

    let gridCol = 2;
    let stageColIdx = 0;
    lastModule = '';
    STAGES.forEach((s, i) => {
      const key = modKey(s.module);
      if (i > 0 && key !== lastModule) {
        const div = document.createElement('div');
        div.className = 'module-divider';
        div.textContent = moduleShort(lastModule);
        div.style.gridRow = `1 / span ${totalRows}`;
        div.style.gridColumn = String(gridCol);
        board.appendChild(div);
        gridCol += 1;
      }
      lastModule = key;
      const hdr = COL_HDR[stageColIdx % 2];
      stageColIdx += 1;
      const header = document.createElement('header');
      header.className = `stage-header ${hdr.bg}`;
      const badge = s.format ? `<span class="badge">${esc(s.format)}</span>` : '';
      header.innerHTML = `<div class="date">${esc(s.dateTime)}</div>
        <h2>${esc(s.title)}</h2>${badge}`;
      header.style.gridRow = '2';
      header.style.gridColumn = String(gridCol);
      board.appendChild(header);
      gridCol += 1;
    });
    ROWS.forEach((r, ri) => {
      const gridRow = ri + 3;
      const rowColor = r.color || '#94a3b8';
      const label = document.createElement('div');
      label.className = 'row-label';
      label.innerHTML = `<strong>${esc(r.title)}</strong>${r.sub ? `<small>${esc(r.sub)}</small>` : ''}`;
      label.style.gridRow = String(gridRow);
      label.style.gridColumn = '1';
      label.style.borderLeftColor = rowColor;
      label.style.background = `linear-gradient(90deg, ${rowTint(rowColor, 0.14)} 0%, var(--surface2) 72%)`;
      board.appendChild(label);
      let dataCol = 2;
      lastModule = '';
      STAGES.forEach((s, si) => {
        const key = modKey(s.module);
        if (si > 0 && key !== lastModule) dataCol += 1;
        lastModule = key;
        const v = s[r.key] || '';
        const empty = !v || v === '—';
        const cell = document.createElement('div');
        cell.className = `cell${empty ? ' empty' : ''}`;
        cell.style.gridRow = String(gridRow);
        cell.style.gridColumn = String(dataCol);
        cell.style.background = rowTint(rowColor, 0.07);
        cell.innerHTML = `<div class="cell-inner">${empty ? '—' : fmt(v)}</div>`;
        board.appendChild(cell);
        dataCol += 1;
      });
    });
    document.getElementById('board').appendChild(board);
    const wrap = document.getElementById('boardWrap');
    wrap.addEventListener('wheel', e => {
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      if (e.shiftKey || e.altKey) { wrap.scrollLeft += e.deltaY; e.preventDefault(); }
    }, { passive: false });
  </script>
</body>
</html>"""


def build_html(cjm_data: dict[str, Any], custom_rows: list[dict[str, str]] | None = None) -> str:
    norm = normalize_cjm(cjm_data, custom_rows)
    title = norm["programTitle"]
    meta = norm["programMeta"]
    stages_js = json.dumps(norm["stages"], ensure_ascii=False)
    rows_js = json.dumps(norm["rows"], ensure_ascii=False)
    groups_js = json.dumps(norm["moduleGroups"], ensure_ascii=False)
    return (
        HTML_TEMPLATE.replace("__TITLE__", title)
        .replace("__META__", meta)
        .replace("__STAGES__", stages_js)
        .replace("__ROWS__", rows_js)
        .replace("__MODULE_GROUPS__", groups_js)
    )
