# -*- coding: utf-8 -*-
"""Клиент GigaChat API (Сбер)."""
from __future__ import annotations

import json
import logging
import time
import uuid
import warnings
from typing import Any

import requests
import urllib3

from .common import (
    JSON_RETRY_USER,
    QUESTIONS_FUNCTION,
    QUESTIONS_SYSTEM_GIGACHAT,
    build_cjm_system_prompt,
    build_cjm_user_prompt,
    build_questions_user_prompt,
    extract_json,
    normalize_questions_result,
    parse_function_arguments,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_BASE = "https://gigachat.devices.sberbank.ru/api/v1"
CHAT_URL = f"{API_BASE}/chat/completions"
MODELS_URL = f"{API_BASE}/models"

DEFAULT_SCOPES = [
    ("GIGACHAT_API_PERS", "Физлица"),
    ("GIGACHAT_API_B2B", "ИП / юрлица (B2B)"),
    ("GIGACHAT_API_CORP", "Корпоративный"),
]

DEFAULT_MODELS = [
    {"id": "GigaChat-2-Max", "name": "GigaChat 2 Max"},
    {"id": "GigaChat-2-Pro", "name": "GigaChat 2 Pro"},
    {"id": "GigaChat-2", "name": "GigaChat 2"},
    {"id": "GigaChat-Max", "name": "GigaChat Max"},
    {"id": "GigaChat-Pro", "name": "GigaChat Pro"},
    {"id": "GigaChat", "name": "GigaChat"},
]

# Безопасный лимит контекста для запросов (символы материалов).
MAX_INPUT_CHARS = 45000

logger = logging.getLogger(__name__)
_token_cache: dict[str, dict[str, Any]] = {}


def _cache_key(auth_key: str, scope: str) -> str:
    return f"{auth_key[:12]}:{scope}"


def get_access_token(auth_key: str, scope: str = "GIGACHAT_API_PERS") -> str:
    key = _cache_key(auth_key, scope)
    cached = _token_cache.get(key)
    if cached and cached["expires_at"] > time.time() + 30:
        return cached["token"]

    r = requests.post(
        OAUTH_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Basic {auth_key}",
            "RqUID": str(uuid.uuid4()),
        },
        data={"scope": scope},
        verify=False,
        timeout=30,
    )
    if not r.ok:
        err = r.text
        try:
            body = r.json()
            if isinstance(body, dict):
                err = body.get("message") or err
        except ValueError:
            pass
        raise RuntimeError(f"GigaChat OAuth: {err}")

    try:
        data = r.json()
    except ValueError as e:
        raise RuntimeError("GigaChat OAuth: пустой или неверный ответ сервера") from e
    token = data.get("access_token")
    if not token:
        raise RuntimeError("GigaChat OAuth: токен не получен")

    expires_in = int(data.get("expires_at", 0)) or int(data.get("expires_in", 1800))
    if expires_in > 10_000_000:
        # expires_at — unix timestamp
        expires_at = expires_in
    else:
        expires_at = time.time() + expires_in

    _token_cache[key] = {"token": token, "expires_at": expires_at}
    return token


def _bearer_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Request-ID": str(uuid.uuid4()),
    }


def _parse_response_json(response: requests.Response, context: str) -> dict[str, Any]:
    raw = (response.text or "").strip()
    if not raw:
        raise RuntimeError(
            f"GigaChat {context}: пустой ответ сервера (HTTP {response.status_code})"
        )

    if raw.startswith("data:"):
        for line in reversed(raw.splitlines()):
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                continue
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        raise RuntimeError(
            f"GigaChat {context}: не удалось разобрать потоковый ответ"
        )

    try:
        parsed = response.json()
    except ValueError as e:
        preview = raw[:240].replace("\n", " ")
        raise RuntimeError(
            f"GigaChat {context}: неверный формат ответа (HTTP {response.status_code}): {preview}"
        ) from e

    if not isinstance(parsed, dict):
        raise RuntimeError(f"GigaChat {context}: ожидался JSON-объект")
    return parsed


def _extract_assistant_content(data: dict[str, Any]) -> tuple[str, Any | None]:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("GigaChat: в ответе нет choices")

    choice = choices[0] or {}
    message = choice.get("message") or {}
    content = message.get("content")
    function_call = message.get("function_call")

    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text") or part.get("content") or ""))
            elif part:
                parts.append(str(part))
        content = "\n".join(p for p in parts if p)

    if content is None:
        content = choice.get("text") or ""

    content = str(content).strip()
    finish_reason = choice.get("finish_reason") or "unknown"

    if function_call:
        args = function_call.get("arguments")
        if args not in (None, "", {}):
            return content, args

    if content:
        return content, None

    raise RuntimeError(
        f"GigaChat вернул пустой ответ (finish_reason={finish_reason}). "
        "Попробуйте GigaChat-2-Pro или сократите документы."
    )


def _api_error_message(response: requests.Response) -> str:
    raw = (response.text or "").strip()
    if not raw:
        return f"HTTP {response.status_code}"
    try:
        body = response.json()
        if isinstance(body, dict):
            return (
                str(body.get("message") or "")
                or str(body.get("error", {}).get("message", ""))
                or str(body)
            )
    except ValueError:
        pass
    return raw[:500]


def fetch_models(auth_key: str, scope: str = "GIGACHAT_API_PERS") -> list[dict[str, str]]:
    token = get_access_token(auth_key, scope)
    try:
        r = requests.get(
            MODELS_URL,
            headers=_bearer_headers(token),
            verify=False,
            timeout=30,
        )
        r.raise_for_status()
        payload = r.json()
        raw = payload.get("data") or payload.get("models") or []
        models = []
        for m in raw:
            mid = m.get("id") or m.get("name")
            if not mid:
                continue
            models.append({"id": mid, "name": m.get("name") or mid})
        if models:
            return sorted(models, key=lambda x: x["id"])
    except Exception:
        pass
    return list(DEFAULT_MODELS)


def chat_completion(
    auth_key: str,
    model: str,
    messages: list[dict[str, str]],
    scope: str = "GIGACHAT_API_PERS",
    temperature: float = 0.4,
    max_tokens: int = 8000,
    *,
    functions: list[dict[str, Any]] | None = None,
    function_call: Any | None = None,
    json_mode: bool = False,
) -> tuple[str, Any | None]:
    token = get_access_token(auth_key, scope)
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "profanity_check": False,
    }

    if functions:
        payload["functions"] = functions
        payload["function_call"] = function_call or "auto"
    else:
        payload["function_call"] = "none"
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

    r = requests.post(
        CHAT_URL,
        headers=_bearer_headers(token),
        json=payload,
        verify=False,
        timeout=300,
    )
    if not r.ok:
        err = _api_error_message(r)
        if json_mode and "response_format" in err.lower():
            return chat_completion(
                auth_key,
                model,
                messages,
                scope,
                temperature,
                max_tokens,
                functions=functions,
                function_call=function_call,
                json_mode=False,
            )
        raise RuntimeError(f"GigaChat: {err}")

    data = _parse_response_json(r, "chat/completions")
    return _extract_assistant_content(data)


def _parse_structured_response(
    content: str,
    function_args: Any | None,
    *,
    normalize_questions: bool = False,
) -> dict[str, Any]:
    if function_args is not None:
        logger.debug("GigaChat function_args: %s", function_args)
        parsed = parse_function_arguments(function_args)
    else:
        logger.debug("GigaChat content preview: %s", (content or "")[:500])
        parsed = extract_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("ИИ вернул JSON не в виде объекта")
    if normalize_questions:
        return normalize_questions_result(parsed)
    return parsed


def _chat_json_with_retry(
    auth_key: str,
    model: str,
    messages: list[dict[str, str]],
    scope: str,
    temperature: float,
    max_tokens: int,
    *,
    functions: list[dict[str, Any]] | None = None,
    function_call: Any | None = None,
    normalize_questions: bool = False,
) -> dict[str, Any]:
    thread = [dict(m) for m in messages]
    last_error: Exception | None = None
    use_functions = functions is not None

    for attempt in range(4):
        call_functions = functions if use_functions and attempt == 0 else None
        call_function_name = function_call if call_functions else None
        temp = temperature if attempt < 2 else max(0.1, temperature - 0.15)
        content = ""
        function_args = None

        try:
            content, function_args = chat_completion(
                auth_key,
                model,
                thread,
                scope,
                temp,
                max_tokens,
                functions=call_functions,
                function_call=call_function_name,
                json_mode=call_functions is None,
            )
            return _parse_structured_response(
                content, function_args, normalize_questions=normalize_questions
            )
        except RuntimeError as e:
            last_error = e
            if attempt == 0 and use_functions:
                use_functions = False
                continue
            if attempt >= 3:
                break
            thread = [dict(m) for m in messages]
            continue
        except ValueError as e:
            last_error = e
            if attempt >= 3:
                break
            assistant_text = content
            if not assistant_text and function_args is not None:
                assistant_text = json.dumps(function_args, ensure_ascii=False)
            thread.append({"role": "assistant", "content": assistant_text})
            thread.append({"role": "user", "content": JSON_RETRY_USER})

    raise RuntimeError(str(last_error or "Не удалось получить JSON от GigaChat"))


def ask_clarifying_questions(
    auth_key: str,
    model: str,
    synthesized: str,
    scope: str = "GIGACHAT_API_PERS",
    columns_detail: str = "",
) -> dict[str, Any]:
    return _chat_json_with_retry(
        auth_key,
        model,
        [
            {"role": "system", "content": QUESTIONS_SYSTEM_GIGACHAT},
            {
                "role": "user",
                "content": build_questions_user_prompt(
                    synthesized[:MAX_INPUT_CHARS], columns_detail
                ),
            },
        ],
        scope,
        temperature=0.2,
        max_tokens=4000,
        functions=[QUESTIONS_FUNCTION],
        function_call={"name": QUESTIONS_FUNCTION["name"]},
        normalize_questions=True,
    )


def generate_cjm(
    auth_key: str,
    model: str,
    synthesized: str,
    answers: dict[str, str],
    scope: str = "GIGACHAT_API_PERS",
    cjm_rows: list[dict[str, str]] | None = None,
    columns_detail: str = "",
) -> dict[str, Any]:
    rows = cjm_rows or []
    answers_text = "\n".join(
        f"- {qid}: {ans}" for qid, ans in answers.items() if ans.strip()
    )
    return _chat_json_with_retry(
        auth_key,
        model,
        [
            {"role": "system", "content": build_cjm_system_prompt(rows, columns_detail)},
            {
                "role": "user",
                "content": build_cjm_user_prompt(
                    synthesized[:MAX_INPUT_CHARS], answers_text, columns_detail
                ),
            },
        ],
        scope,
        temperature=0.25,
        max_tokens=8000,
    )
