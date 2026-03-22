from __future__ import annotations

from fastapi import FastAPI
from ai_hedge_bot.app.main import create_app

# PhaseG integrated app. Existing tests importing `app` continue to work.
app: FastAPI = create_app()
