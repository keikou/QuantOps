import asyncio

from app.clients.v12_client import V12Client


async def _main():
    client = V12Client(base_url="http://localhost:8000", mock_mode=True)
    risk = await client.get_risk_budget()
    execution = await client.get_execution_quality()
    diagnostics = await client.get_portfolio_diagnostics()
    health = await client.get_system_health()
    shadow = await client.get_shadow_summary()
    portfolio = await client.get_portfolio_dashboard()

    assert "risk" in risk
    assert "fill_rate" in execution
    assert ("diagnostics" in diagnostics) or ("latest" in diagnostics)
    assert "status" in health
    assert "net_shadow_pnl" in shadow
    assert ('quotes_as_of' in portfolio) or ('summary' in portfolio) or ('snapshot' in portfolio)


def test_v12_client_compat_methods():
    asyncio.run(_main())
