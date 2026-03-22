from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get('/me')
def me() -> dict:
    return {
        'id': 'local-admin',
        'name': 'Local Admin',
        'email': 'local-admin@example.com',
        'role': 'admin',
        'status': 'ok',
    }
