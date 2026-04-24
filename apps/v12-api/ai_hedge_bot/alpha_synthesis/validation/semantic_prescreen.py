from __future__ import annotations


def semantic_prescreen(metrics: dict[str, float | bool]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not bool(metrics.get("output_exists")):
        reasons.append("no_output")
    if bool(metrics.get("all_null")):
        reasons.append("all_null_output")
    if bool(metrics.get("constant_like")):
        reasons.append("constant_like_expression")
    if float(metrics.get("variance_score", 0.0) or 0.0) < 0.05:
        reasons.append("variance_below_threshold")
    if float(metrics.get("instability_score", 0.0) or 0.0) > 0.24:
        reasons.append("instability_too_high")
    if float(metrics.get("turnover_proxy", 0.0) or 0.0) > 0.45:
        reasons.append("turnover_proxy_too_high")
    return ("accepted" if not reasons else "rejected", reasons)

