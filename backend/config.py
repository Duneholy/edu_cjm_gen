# -*- coding: utf-8 -*-
"""Конфигурация приложения."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SECRET_KEY = "cjm-generator-local"
HOST = "127.0.0.1"
PORT = 5050
