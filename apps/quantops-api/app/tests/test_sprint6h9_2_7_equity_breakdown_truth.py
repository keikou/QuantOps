from app.services.equity_breakdown import compute_equity_breakdown


def test_breakdown_prefers_truth_total_equity_and_available_margin_model() -> None:
    payload = compute_equity_breakdown(
        {
            'summary': {
                'cash_balance': 103000.0,
                'used_margin': 17000.0,
                'unrealized_pnl': 600.0,
                'total_equity': 100600.0,
            }
        },
        {
            'items': [
                {'qty': 0.1, 'avg_price': 70000.0, 'pnl': 100.0},
                {'qty': 5.0, 'avg_price': 2000.0, 'pnl': 500.0},
            ]
        },
    )
    assert payload['balance'] == 103000.0
    assert payload['used_margin'] == 17000.0
    assert payload['unrealized'] == 600.0
    assert payload['total_equity'] == 100600.0
    assert payload['free_margin'] == 83600.0


def test_breakdown_derives_total_equity_from_cash_plus_mark_to_market_when_missing() -> None:
    payload = compute_equity_breakdown(
        {
            'summary': {
                'cash_balance': 50000.0,
            }
        },
        {
            'items': [
                {'signed_qty': 2.0, 'avg_entry_price': 10000.0, 'mark_price': 11000.0, 'unrealized_pnl': 2000.0},
                {'signed_qty': -1.0, 'avg_entry_price': 5000.0, 'mark_price': 4500.0, 'unrealized_pnl': 500.0},
            ]
        },
    )
    assert payload['balance'] == 50000.0
    assert payload['used_margin'] == 25000.0
    assert payload['unrealized'] == 2500.0
    assert payload['total_equity'] == 67500.0
    assert payload['free_margin'] == 42500.0
