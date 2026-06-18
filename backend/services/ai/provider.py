# -*- coding: utf-8 -*-
"""Единый интерфейс для ИИ-провайдеров."""
from __future__ import annotations

from typing import Any

from . import gigachat, openrouter

PROVIDERS = {
    "openrouter": {
        "label": "OpenRouter",
        "credentialLabel": "API-ключ",
        "credentialPlaceholder": "sk-or-v1-...",
    },
    "gigachat": {
        "label": "GigaChat API",
        "credentialLabel": "Authorization Key",
        "credentialPlaceholder": "MDE5Yzk5Zjkt...",
    },
}


def fetch_models(provider: str, credential: str, scope: str | None = None) -> list[dict[str, str]]:
    if provider == "gigachat":
        return gigachat.fetch_models(credential, scope or "GIGACHAT_API_PERS")
    return openrouter.fetch_models(credential)


def ask_clarifying_questions(
    provider: str,
    credential: str,
    model: str,
    synthesized: str,
    scope: str | None = None,
    columns_detail: str = "",
) -> dict[str, Any]:
    if provider == "gigachat":
        return gigachat.ask_clarifying_questions(
            credential, model, synthesized, scope or "GIGACHAT_API_PERS", columns_detail
        )
    return openrouter.ask_clarifying_questions(credential, model, synthesized, columns_detail)


def generate_cjm(
    provider: str,
    credential: str,
    model: str,
    synthesized: str,
    answers: dict[str, str],
    scope: str | None = None,
    cjm_rows: list[dict[str, str]] | None = None,
    columns_detail: str = "",
) -> dict[str, Any]:
    if provider == "gigachat":
        return gigachat.generate_cjm(
            credential,
            model,
            synthesized,
            answers,
            scope or "GIGACHAT_API_PERS",
            cjm_rows,
            columns_detail,
        )
    return openrouter.generate_cjm(
        credential, model, synthesized, answers, cjm_rows, columns_detail
    )
