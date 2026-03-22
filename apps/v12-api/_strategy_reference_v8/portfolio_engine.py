def build_targets(forecasts: list[dict], budgeted: dict) -> dict:
    targets = {}
    for f in forecasts:
        st = f["strategy_id"]
        if st not in budgeted:
            continue
        weight = budgeted[st]["budgeted_score"]
        targets[f["symbol"]] = round(targets.get(f["symbol"], 0.0) + weight, 6)
    gross = round(sum(abs(v) for v in targets.values()), 6)
    net = round(sum(targets.values()), 6)
    return {"targets": targets, "gross_exposure": gross, "net_exposure": net}
