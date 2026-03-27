from app.services.equity_breakdown import compute_equity_breakdown


def test_equity_breakdown_basic():
    dashboard = {
        "summary": {
            "balance": 100,
        }
    }

    positions = {
        "items": [
            {
                "signed_qty": 1,
                "avg_entry_price": 100,
                "mark_price": 110,
                "unrealized_pnl": 10,
            }
        ]
    }

    result = compute_equity_breakdown(dashboard, positions)

    assert result["total_equity"] == 210
    assert result["unrealized"] == 10