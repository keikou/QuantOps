from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get('/current')
def current_config() -> dict:
    settings = get_settings()
    return {
        'status': 'ok',
        'environment': 'local',
        'current': {
            'app_name': settings.app_name,
            'app_version': settings.app_version,
            'api_prefix': settings.api_prefix,
            'db_path': settings.db_path,
            'v12_base_url': settings.v12_base_url,
            'v12_mock_mode': settings.v12_mock_mode,
            'risk_refresh_interval_seconds': settings.risk_refresh_interval_seconds,
            'quantops_public_port': settings.quantops_public_port,
        },
    }
