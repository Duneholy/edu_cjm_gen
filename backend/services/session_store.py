# -*- coding: utf-8 -*-
"""In-memory хранилище сессий генерации."""
from __future__ import annotations

from typing import Any

SESSIONS: dict[str, dict[str, Any]] = {}


def get(session_id: str) -> dict[str, Any] | None:
    return SESSIONS.get(session_id)


def set(session_id: str, data: dict[str, Any]) -> None:
    SESSIONS[session_id] = data


def update(session_id: str, **fields: Any) -> None:
    if session_id in SESSIONS:
        SESSIONS[session_id].update(fields)
