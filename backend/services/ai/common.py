# -*- coding: utf-8 -*-
"""Общие промпты и утилиты для ИИ-провайдеров."""
from __future__ import annotations

import json
import re
from typing import Any

QUESTIONS_SYSTEM_GIGACHAT = """Ты — эксперт по образовательным продуктам и Customer Journey Map (CJM).
На основе входных материалов сформулируй уточняющие вопросы для построения CJM.

Вызови функцию submit_questions. В каждом элементе questions обязательно заполни поле question — полный текст вопроса.

Правила:
- Не более 5 вопросов
- Вопросы конкретные, про формат, роли, этапы, артефакты, аудиторию, наставников
- Если информации достаточно — 2-3 вопроса на критичные пробелы
- Язык: русский"""

QUESTIONS_SYSTEM = """Ты — эксперт по образовательным продуктам и Customer Journey Map (CJM).
На основе входных материалов сформулируй уточняющие вопросы для построения CJM.

Ответь СТРОГО валидным JSON без markdown:
{
  "programSummary": "краткое резюме программы в 2-3 предложения",
  "detectedGaps": ["что неясно или противоречиво"],
  "questions": [
    {"id": "q1", "question": "текст вопроса", "hint": "зачем нужен ответ"}
  ]
}

Правила:
- Не более 5 вопросов
- В каждом объекте questions поле question — обязательно и непустое
- Вопросы конкретные, про формат, роли, этапы, артефакты, аудиторию, наставников
- Если информации достаточно — 2-3 вопроса на критичные пробелы
- Язык: русский"""

QUESTIONS_FUNCTION = {
    "name": "submit_questions",
    "description": "Вернуть резюме программы, пробелы и уточняющие вопросы для CJM",
    "parameters": {
        "type": "object",
        "properties": {
            "programSummary": {
                "type": "string",
                "description": "Краткое резюме программы в 2-3 предложения",
            },
            "detectedGaps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Что неясно или противоречиво в материалах",
            },
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Идентификатор, например q1"},
                        "question": {
                            "type": "string",
                            "description": "Полный текст уточняющего вопроса пользователю",
                        },
                        "hint": {
                            "type": "string",
                            "description": "Краткая подсказка, зачем нужен ответ",
                        },
                    },
                    "required": ["id", "question"],
                },
            },
        },
        "required": ["programSummary", "questions"],
    },
}

JSON_RETRY_USER = (
    "Предыдущий ответ невалиден. Верни ТОЛЬКО один JSON-объект. "
    "Без markdown, без комментариев до или после JSON. Начни с { и закончи }."
)


def build_questions_user_prompt(synthesized: str, columns_detail: str) -> str:
    return f"""Материалы проекта:

{synthesized[:120000]}

Требования к столбцам CJM (детализация):
{columns_detail or "(не указано)"}

Сформулируй уточняющие вопросы для построения CJM."""


def build_cjm_system_prompt(rows: list[dict[str, str]], columns_detail: str = "") -> str:
    rows_desc = "\n".join(
        f'- key "{r["key"]}": {r["title"]}' for r in rows
    )
    stage_fields = ",\n      ".join(
        f'"{r["key"]}": "markdown-содержание для строки: {r["title"]}"'
        for r in rows
    )
    rows_json = json.dumps(
        [{"key": r["key"], "title": r["title"], "sub": r.get("sub", "")} for r in rows],
        ensure_ascii=False,
        indent=2,
    )
    return f"""Ты — эксперт по CJM для образовательных программ.
Собери полную Customer Journey Map в JSON для визуализации.

Строки CJM (обязательные поля в каждом этапе):
{rows_desc}

Требования к столбцам (этапам) CJM:
{columns_detail or "Сбалансированная детализация по материалам проекта."}

Ответь СТРОГО валидным JSON (без markdown):
{{
  "programTitle": "название программы",
  "programMeta": "краткое описание для шапки (аудитория, формат, длительность)",
  "rows": {rows_json},
  "stages": [
    {{
      "col": "1. Название колонки",
      "module": "Название группы / модуля (одинаковое у соседних столбцов одного этапа программы)",
      "dateTime": "дата или период",
      "title": "Этап CJM",
      "format": "индивидуально / в паре / ...",
      {stage_fields},
      "color": "#0284c7"
    }}
  ]
}}

Правила:
- Включи этапы ДО старта (сбор заявок, тест, распределение) если уместно
- Количество и детализация столбцов (stages) — строго по требованиям к столбцам выше
- Поле module — общее имя группы для соседних столбцов одного модуля/этапа (например «Модуль 1. Рынок и идея» для нескольких занятий); у каждого столбца внутри группы своё title
- Если модуль не назван в материалах — используй «Этап 1», «Этап 2» и т.д.
- Верхнеуровневая карта: 5–10 столбцов по модулям/крупным этапам; подробная: отдельный столбец на каждый урок/занятие
- В КАЖДОМ stage заполни ВСЕ ключи строк: {", ".join(r["key"] for r in rows)}
- Цвета color по этапам: до старта #64748b, этап 0 #0ea5e9, 1 #0284c7, 2 #7c3aed, 3 #d97706, 4 #059669
- Тексты содержательные, как в профессиональной CJM для заказчика
- Используй markdown внутри полей: списки -, таблицы |, **жирный**
- Если данных нет — ставь «—»
- Язык: русский
- Ответ — ТОЛЬКО JSON-объект, без markdown и пояснений"""


def extract_json(text: str) -> Any:
    if not text or not str(text).strip():
        raise ValueError("ИИ вернул пустой ответ — не удалось разобрать JSON")

    text = str(text).strip().lstrip("\ufeff")
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        text = m.group(1).strip()

    if not text:
        raise ValueError("ИИ вернул пустой JSON-блок")

    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                continue

    raise ValueError(
        "ИИ вернул ответ без JSON-объекта. Попробуйте другую модель или сократите документы."
    )


def parse_function_arguments(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str) and arguments.strip():
        parsed = extract_json(arguments)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("ИИ вернул некорректные аргументы функции")


def _pick_field(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def normalize_questions_result(data: dict[str, Any]) -> dict[str, Any]:
    """Приводит ответ разных моделей к единому формату questions."""
    if len(data) == 1:
        wrapped = next(iter(data.values()))
        if isinstance(wrapped, dict):
            data = wrapped

    program_summary = _pick_field(
        data,
        ("programSummary", "program_summary", "summary", "резюме", "program_summary_text"),
    )
    detected_gaps: list[str] = []
    for key in ("detectedGaps", "detected_gaps", "gaps", "пробелы"):
        raw_gaps = data.get(key)
        if isinstance(raw_gaps, list):
            detected_gaps = [str(g).strip() for g in raw_gaps if str(g).strip()]
            break

    raw_questions = data.get("questions") or data.get("вопросы") or []
    questions: list[dict[str, str]] = []

    for index, item in enumerate(raw_questions[:5]):
        if isinstance(item, str) and item.strip():
            questions.append(
                {
                    "id": f"q{index + 1}",
                    "question": item.strip(),
                    "hint": "",
                }
            )
            continue

        if not isinstance(item, dict):
            continue

        text = _pick_field(
            item,
            ("question", "text", "title", "content", "вопрос", "query", "name", "message"),
        )
        hint = _pick_field(item, ("hint", "help", "подсказка", "description", "context"))
        qid = _pick_field(item, ("id", "key", "code")) or f"q{index + 1}"

        if not text:
            for key, value in item.items():
                if key in ("id", "key", "code", "hint", "help", "подсказка"):
                    continue
                if isinstance(value, str) and value.strip():
                    text = value.strip()
                    break
                if isinstance(value, str) and not hint:
                    hint = key.strip()

        if text:
            questions.append({"id": qid, "question": text, "hint": hint})

    if not questions:
        raise ValueError(
            "ИИ вернул пустые вопросы (нет текста в поле question). "
            "Попробуйте GigaChat-2-Pro или повторите анализ."
        )

    return {
        "programSummary": program_summary,
        "detectedGaps": detected_gaps,
        "questions": questions,
    }


def build_cjm_user_prompt(
    synthesized: str,
    answers_text: str,
    columns_detail: str = "",
) -> str:
    return f"""Материалы проекта:

{synthesized[:100000]}

Требования к столбцам CJM:
{columns_detail or "(не указано)"}

Ответы на уточняющие вопросы:
{answers_text or "(без дополнительных ответов)"}

Собери полную CJM."""
