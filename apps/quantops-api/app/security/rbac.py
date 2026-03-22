from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status


ROLE_RANK = {
    'viewer': 1,
    'operator': 2,
    'risk_manager': 3,
    'admin': 4,
}


@dataclass(frozen=True)
class RequestActor:
    user_id: str
    role: str


def get_request_actor(
    x_user_id: str | None = Header(default='system-admin', alias='X-User-Id'),
    x_user_role: str | None = Header(default='admin', alias='X-User-Role'),
) -> RequestActor:
    role = (x_user_role or 'viewer').strip().lower()
    if role not in ROLE_RANK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Unknown role: {role}')
    return RequestActor(user_id=(x_user_id or 'viewer').strip() or 'viewer', role=role)


def require_role(actor: RequestActor, minimum_role: str) -> RequestActor:
    if ROLE_RANK[actor.role] < ROLE_RANK[minimum_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{minimum_role} role required for this action',
        )
    return actor
