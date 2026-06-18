# -*- coding: utf-8 -*-
"""Страницы приложения."""
from flask import Blueprint, render_template

from backend.services.ai.provider import PROVIDERS

bp = Blueprint("pages", __name__)


@bp.route("/")
def index():
    return render_template("index.html", providers=PROVIDERS)
