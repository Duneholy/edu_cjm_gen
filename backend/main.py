# -*- coding: utf-8 -*-
"""
CJM Generator — точка сборки приложения.
Тонкий entry point: регистрирует blueprints и раздаёт frontend.
"""
from __future__ import annotations

import logging

from flask import Flask

from backend.config import FRONTEND_DIR, SECRET_KEY
from backend.routers import analyze, generate, models, pages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR),
        static_folder=str(FRONTEND_DIR),
        static_url_path="",
    )
    app.secret_key = SECRET_KEY

    app.register_blueprint(pages.bp)
    app.register_blueprint(models.bp)
    app.register_blueprint(analyze.bp)
    app.register_blueprint(generate.bp)

    return app
