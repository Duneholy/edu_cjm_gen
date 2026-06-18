# -*- coding: utf-8 -*-
"""Клиент OpenRouter API."""
from __future__ import annotations

from typing import Any

import requests

from .common import (
    QUESTIONS_SYSTEM,
    build_cjm_system_prompt,
    build_cjm_user_prompt,
    build_questions_user_prompt,
    extract_json,
    normalize_questions_result,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"

DEFAULT_MODELS = [
    "qwen/qwen3.7-plus",
    "qwen/qwen3-235b-a22b-instruct-2507",
    "qwen/qwen3-32b",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-flash-preview",
    "openai/gpt-4.1-mini",
]


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5050",
        "X-Title": "CJM Generator",
    }


def fetch_models(api_key: str) -> list[dict[str, str]]:
    try:
        r = requests.get(MODELS_URL, headers=_headers(api_key), timeout=30)
        r.raise_for_status()
        data = r.json().get("data", [])
        models = sorted(
            [
                {"id": m["id"], "name": m.get("name", m["id"])}
                for m in data
                if m.get("id")
            ],
            key=lambda x: x["id"],
        )
        if models:
            return models
    except Exception:
        pass
    return [{"id": m, "name": m} for m in DEFAULT_MODELS]


def chat_completion(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 16000,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    r = requests.post(
        OPENROUTER_URL,
        headers=_headers(api_key),
        json=payload,
        timeout=180,
    )
    if not r.ok:
        err = r.text
        try:
            err = r.json().get("error", {}).get("message", err)
        except Exception:
            pass
        raise RuntimeError(f"OpenRouter: {err}")
    data = r.json()
    choice = data.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("OpenRouter вернул пустой ответ")
    return content


def ask_clarifying_questions(
    api_key: str,
    model: str,
    synthesized: str,
    columns_detail: str = "",
) -> dict[str, Any]:
    content = chat_completion(
        api_key,
        model,
        [
            {"role": "system", "content": QUESTIONS_SYSTEM},
            {
                "role": "user",
                "content": build_questions_user_prompt(synthesized, columns_detail),
            },
        ],
        temperature=0.3,
        max_tokens=4000,
    )
    return normalize_questions_result(extract_json(content))


def generate_cjm(
    api_key: str,
    model: str,
    synthesized: str,
    answers: dict[str, str],
    cjm_rows: list[dict[str, str]] | None = None,
    columns_detail: str = "",
) -> dict[str, Any]:
    rows = cjm_rows or []
    answers_text = "\n".join(
        f"- {qid}: {ans}" for qid, ans in answers.items() if ans.strip()
    )
    content = chat_completion(
        api_key,
        model,
        [
            {"role": "system", "content": build_cjm_system_prompt(rows, columns_detail)},
            {
                "role": "user",
                "content": build_cjm_user_prompt(synthesized, answers_text, columns_detail),
            },
        ],
        temperature=0.45,
        max_tokens=16000,
    )
    return extract_json(content)
