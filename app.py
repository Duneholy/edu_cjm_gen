# -*- coding: utf-8 -*-
"""Обратная совместимость: python app.py → run.py"""
from run import app

if __name__ == "__main__":
    from backend.config import HOST, PORT
    print(f"CJM Generator: http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
