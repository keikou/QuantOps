from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "QuantOps API"
    app_version: str = "0.3.0"
    api_prefix: str = "/api/v1"
    db_path: str = os.getenv("QUANTOPS_DB_PATH", "./data/quantops.duckdb")
    runtime_dir: Path = Path(os.getenv("QUANTOPS_RUNTIME_DIR", "./runtime"))
    v12_base_url: str = os.getenv("V12_BASE_URL", "http://127.0.0.1:8000")
    v12_timeout_seconds: float = float(os.getenv("V12_TIMEOUT_SECONDS", "10"))
    v12_mock_mode: bool = os.getenv("V12_MOCK_MODE", "true").lower() in {"1", "true", "yes", "on"}
    cors_allow_origins: tuple[str, ...] = tuple(
        filter(None, os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","))
    )
    risk_refresh_interval_seconds: int = int(
        os.getenv("WORKER_INTERVAL_SEC", os.getenv("RISK_REFRESH_INTERVAL_SECONDS", "60"))
    )
    quantops_public_port: int = int(os.getenv("QUANTOPS_PUBLIC_PORT", "8010"))
    command_center_admin_role: str = os.getenv("COMMAND_CENTER_ADMIN_ROLE", "admin")
    command_center_operator_role: str = os.getenv("COMMAND_CENTER_OPERATOR_ROLE", "operator")

    @property
    def log_dir(self) -> Path:
        return self.runtime_dir / "logs"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
