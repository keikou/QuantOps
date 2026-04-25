from __future__ import annotations

RISK_RANK = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
    "L0_NORMAL": 1,
    "L1_WATCH": 1,
    "L2_REDUCE": 2,
    "L3_FREEZE": 3,
    "L4_PARTIAL_HALT": 3,
    "L5_GLOBAL_HALT": 4,
}

DEFAULT_ROLE_CAPS = {
    "VIEWER": "LOW",
    "OPERATOR": "MEDIUM",
    "RISK_MANAGER": "HIGH",
    "EXECUTION_MANAGER": "HIGH",
    "RESEARCH_MANAGER": "HIGH",
    "ADMIN": "CRITICAL",
    "EMERGENCY_CONTROLLER": "CRITICAL",
    "SERVICE_ORC": "HIGH",
    "SERVICE_AES": "MEDIUM",
    "SERVICE_AAE": "MEDIUM",
    "SERVICE_LCC": "HIGH",
    "SERVICE_EXECUTION": "HIGH",
}

SAFETY_WEAKENING_ACTIONS = {
    "resume_scope",
    "policy.relax.risk",
    "policy_relaxation",
    "increase_exposure",
    "alpha.promote",
    "override_halt",
    "override_freeze",
}

