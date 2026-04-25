from __future__ import annotations


APPROVAL_TRANSITIONS = {
    "pending": {"approved", "rejected", "expired"},
    "approved": {"dispatched", "dispatch_failed"},
    "dispatched": {"enforced", "dispatch_failed"},
    "dispatch_failed": {"dispatched", "expired"},
    "rejected": set(),
    "expired": set(),
    "enforced": set(),
}

OVERRIDE_TRANSITIONS = {
    "active": {"expired", "revoked", "blocked"},
    "expired": set(),
    "revoked": set(),
    "blocked": set(),
}


def approval_transition_allowed(current: str, nxt: str) -> bool:
    return nxt in APPROVAL_TRANSITIONS.get(current, set())


def override_transition_allowed(current: str, nxt: str) -> bool:
    return nxt in OVERRIDE_TRANSITIONS.get(current, set())

