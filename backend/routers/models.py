# -*- coding: utf-8 -*-
"""API: список моделей ИИ."""
from flask import Blueprint, jsonify, request

from backend.services.ai.provider import PROVIDERS, fetch_models

bp = Blueprint("models", __name__, url_prefix="/api")


def _validate_provider(provider: str) -> str:
    if provider not in PROVIDERS:
        raise ValueError(f"Неизвестный провайдер: {provider}")
    return provider


@bp.route("/models", methods=["POST"])
def api_models():
    data = request.get_json(silent=True) or {}
    try:
        provider = _validate_provider((data.get("provider") or "openrouter").strip())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    credential = (data.get("credential") or data.get("apiKey") or "").strip()
    scope = (data.get("scope") or "GIGACHAT_API_PERS").strip()

    if not credential:
        label = PROVIDERS[provider]["credentialLabel"]
        return jsonify({"error": f"Укажите {label}"}), 400
    try:
        models = fetch_models(provider, credential, scope)
        return jsonify({"models": models, "provider": provider})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
