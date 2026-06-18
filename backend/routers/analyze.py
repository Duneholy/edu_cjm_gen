# -*- coding: utf-8 -*-
"""API: анализ документов и уточняющие вопросы."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import logging

from flask import Blueprint, jsonify, request

from backend.services.ai.common import normalize_questions_result
from backend.services.ai.provider import PROVIDERS, ask_clarifying_questions
from backend.services.cjm_rows import parse_rows_payload
from backend.services.document_parser import ALLOWED_EXT, parse_file, synthesize_documents
from backend.services.session_store import set as save_session

bp = Blueprint("analyze", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def _validate_provider(provider: str) -> str:
    if provider not in PROVIDERS:
        raise ValueError(f"Неизвестный провайдер: {provider}")
    return provider


@bp.route("/analyze", methods=["POST"])
def api_analyze():
    try:
        provider = _validate_provider((request.form.get("provider") or "openrouter").strip())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    credential = (request.form.get("credential") or request.form.get("apiKey") or "").strip()
    model = (request.form.get("model") or "").strip()
    scope = (request.form.get("scope") or "GIGACHAT_API_PERS").strip()

    if not credential:
        label = PROVIDERS[provider]["credentialLabel"]
        return jsonify({"error": f"Укажите {label}"}), 400

    if not model:
        model = "GigaChat-2-Pro" if provider == "gigachat" else "qwen/qwen3.7-plus"

    files = {
        "brief": request.files.get("brief"),
        "concept": request.files.get("concept"),
        "details": request.files.get("details"),
    }
    for name in ("brief", "concept"):
        f = files[name]
        if not f or not f.filename:
            return jsonify({"error": f"Загрузите файл: {name}"}), 400

    parsed: dict[str, str] = {"details": ""}
    try:
        for key in ("brief", "concept"):
            f = files[key]
            ext = Path(f.filename).suffix.lower()
            if ext not in ALLOWED_EXT:
                return jsonify(
                    {"error": f"Файл {key}: формат {ext} не поддерживается"}
                ), 400
            parsed[key] = parse_file(f.filename, f.read())

        details_file = files["details"]
        if details_file and details_file.filename:
            ext = Path(details_file.filename).suffix.lower()
            if ext not in ALLOWED_EXT:
                return jsonify(
                    {"error": f"Файл details: формат {ext} не поддерживается"}
                ), 400
            parsed["details"] = parse_file(details_file.filename, details_file.read())
    except Exception as e:
        return jsonify({"error": f"Ошибка чтения файлов: {e}"}), 400

    try:
        cjm_rows = parse_rows_payload(request.form.get("cjmRows"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    columns_detail = (request.form.get("cjmColumnsDetail") or "").strip()
    if not columns_detail:
        return jsonify({"error": "Укажите степень детализации столбцов CJM"}), 400

    synthesized = synthesize_documents(
        parsed["brief"], parsed["concept"], parsed["details"]
    )

    try:
        ai_result = ask_clarifying_questions(
            provider, credential, model, synthesized, scope, columns_detail
        )
        ai_result = normalize_questions_result(ai_result)
    except Exception as e:
        logger.exception("Analyze AI failed: provider=%s model=%s", provider, model)
        return jsonify({"error": f"Ошибка ИИ: {e}"}), 500

    questions = ai_result.get("questions", [])[:5]
    logger.info(
        "Analyze OK: provider=%s model=%s questions=%s summary_len=%s",
        provider,
        model,
        len(questions),
        len(ai_result.get("programSummary", "")),
    )
    session_id = str(uuid.uuid4())
    save_session(
        session_id,
        {
            "synthesized": synthesized,
            "provider": provider,
            "credential": credential,
            "model": model,
            "scope": scope,
            "cjm_rows": cjm_rows,
            "cjm_columns_detail": columns_detail,
            "questions": questions,
            "created": datetime.now(timezone.utc).isoformat(),
        },
    )

    return jsonify(
        {
            "sessionId": session_id,
            "programSummary": ai_result.get("programSummary", ""),
            "detectedGaps": ai_result.get("detectedGaps", []),
            "questions": questions,
            "previewLength": len(synthesized),
            "provider": provider,
        }
    )
