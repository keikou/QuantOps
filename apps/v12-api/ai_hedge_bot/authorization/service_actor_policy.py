from __future__ import annotations


class ServiceActorPolicy:
    def denied(self, actor_type: str, roles: list[str], action: str, source_system: str) -> str:
        if actor_type != "service":
            return ""
        if action.startswith("approval.approve"):
            return "service_actor_cannot_approve"
        if "SERVICE_EXECUTION" in roles and action in {"override.create.high", "override.create.critical", "dispatch.execute"}:
            return "service_execution_cannot_bypass_enforcement"
        if "SERVICE_AAE" in roles and action == "alpha.promote":
            return "service_aae_cannot_self_approve_promotion"
        if "SERVICE_AES" in roles and action.startswith("policy.apply"):
            return "service_aes_cannot_self_apply_policy"
        return ""

