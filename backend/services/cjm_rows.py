# -*- coding: utf-8 -*-
"""Конфигурация строк CJM."""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

ROW_COLORS = [
    "#38bdf8",
    "#a78bfa",
    "#fbbf24",
    "#f87171",
    "#34d399",
    "#f472b6",
    "#22d3ee",
    "#c084fc",
    "#fb923c",
    "#4ade80",
]

DEFAULT_ROWS: list[dict[str, str]] = [
    {"key": "student_action", "title": "Пользовательское действие (ученик)"},
    {"key": "mentor_action", "title": "Пользовательское действие (наставник)"},
    {"key": "motivation", "title": "Мотивация (цели ученика)"},
    {"key": "problems", "title": "Проблемы (барьеры, с которыми сталкивается ученик)"},
    {"key": "artifacts", "title": "Артефакты (материалы и формы, присутствующие на этапе)"},
    {"key": "contacts", "title": "Контакты (точки контакта с учеником)"},
]


def _slug_key(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", title.lower().strip())[:40].strip("_")
    return base or f"row_{uuid.uuid4().hex[:8]}"


def parse_rows_payload(raw: str | list | None) -> list[dict[str, str]]:
    if raw is None:
        return [dict(r) for r in DEFAULT_ROWS]
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return [dict(r) for r in DEFAULT_ROWS]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Некорректный JSON строк CJM: {e}") from e
    else:
        data = raw

    if not isinstance(data, list) or not data:
        raise ValueError("Строки CJM: нужен непустой массив")

    rows: list[dict[str, str]] = []
    used_keys: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        key = (item.get("key") or "").strip() or _slug_key(title)
        if key in used_keys:
            key = f"{key}_{len(used_keys)}"
        used_keys.add(key)
        rows.append({"key": key, "title": title, "sub": (item.get("sub") or "").strip()})

    if not rows:
        raise ValueError("Добавьте хотя бы одну строку CJM")
    return rows


def enrich_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    enriched = []
    for i, row in enumerate(rows):
        enriched.append(
            {
                "key": row["key"],
                "title": row["title"],
                "sub": row.get("sub", ""),
                "color": ROW_COLORS[i % len(ROW_COLORS)],
            }
        )
    return enriched


def apply_rows_to_cjm(cjm_data: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    """Подставляет пользовательские строки и гарантирует поля в каждом этапе."""
    display_rows = enrich_rows(rows)
    cjm_data["rows"] = display_rows
    for stage in cjm_data.get("stages", []):
        for row in display_rows:
            if row["key"] not in stage or not str(stage.get(row["key"], "")).strip():
                stage[row["key"]] = stage.get(row["key"]) or "—"
    return cjm_data
