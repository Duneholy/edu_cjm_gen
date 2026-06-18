# -*- coding: utf-8 -*-
"""API: генерация CJM и выдача HTML."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from backend.config import OUTPUT_DIR
from backend.services.ai.provider import generate_cjm
from backend.services.cjm_builder import build_html
from backend.services.cjm_rows import apply_rows_to_cjm
from backend.services.session_store import get as get_session
from backend.services.session_store import update as update_session

bp = Blueprint("generate", __name__, url_prefix="/api")


@bp.route("/generate", methods=["POST"])
def api_generate():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("sessionId") or "").strip()
    answers = data.get("answers") or {}

    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Сессия не найдена. Начните заново."}), 404

    try:
        cjm_data = generate_cjm(
            session["provider"],
            session["credential"],
            session["model"],
            session["synthesized"],
            answers,
            session.get("scope"),
            session.get("cjm_rows"),
            session.get("cjm_columns_detail", ""),
        )
        cjm_data = apply_rows_to_cjm(cjm_data, session.get("cjm_rows") or [])
    except Exception as e:
        return jsonify({"error": f"Ошибка генерации CJM: {e}"}), 500

    html = build_html(cjm_data, session.get("cjm_rows"))
    slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"cjm_{slug}.html"
    out_path.write_text(html, encoding="utf-8")

    update_session(session_id, html_path=str(out_path), cjm_data=cjm_data)

    return jsonify(
        {
            "success": True,
            "stagesCount": len(cjm_data.get("stages", [])),
            "programTitle": cjm_data.get("programTitle", "CJM"),
            "viewUrl": f"/api/view/{slug}",
            "downloadUrl": f"/api/download/{slug}",
        }
    )


@bp.route("/view/<slug>")
def api_view(slug):
    path = OUTPUT_DIR / f"cjm_{slug}.html"
    if not path.exists():
        return "Файл не найден", 404
    return send_file(path, mimetype="text/html")


@bp.route("/download/<slug>")
def api_download(slug):
    path = OUTPUT_DIR / f"cjm_{slug}.html"
    if not path.exists():
        return "Файл не найден", 404
    return send_file(path, as_attachment=True, download_name=path.name)
