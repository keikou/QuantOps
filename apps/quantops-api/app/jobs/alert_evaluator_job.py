from app.core.deps import get_alert_service


def run():

    return get_alert_service().evaluate_rules()


def evaluate_alerts():

    return run()