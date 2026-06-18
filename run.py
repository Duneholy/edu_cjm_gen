# -*- coding: utf-8 -*-
"""Запуск CJM Generator."""
import os

from backend.config import HOST, PORT
from backend.main import create_app

app = create_app()

if __name__ == "__main__":
    # Через run_windows.bat: без reloader — один процесс, Ctrl+C останавливает сервер
    launcher = os.environ.get("CJM_LAUNCHER") == "1"
    debug = not launcher and os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"CJM Generator: http://{HOST}:{PORT}")
    if launcher:
        print("Нажмите Ctrl+C в этом окне, чтобы остановить сервер.")
    app.run(host=HOST, port=PORT, debug=debug, use_reloader=debug)