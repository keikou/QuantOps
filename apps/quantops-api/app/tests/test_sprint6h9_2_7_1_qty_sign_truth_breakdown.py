from app.services.equity_breakdown import compute_equity_breakdown


def test_breakdown_uses_v12_total_equity_and_unclamped_free_margin() -> None:
    payload = compute_equity_breakdown(
        {
            'summary': {
                'cash_balance': 109990.0,
                'used_margin': 10000.0,
                'unrealized_pnl': 500.0,
                'total_equity': 100500.0,
            }
        },
        {
            'items': [
                {'signed_qty': -5.0, 'avg_entry_price': 2000.0, 'unrealized_pnl': 500.0},
            ]
        },
    )
    assert payload['balance'] == 109990.0
    assert payload['used_margin'] == 10000.0
    assert payload['unrealized'] == 500.0
    assert payload['total_equity'] == 100500.0
    assert payload['free_margin'] == 90500.0
