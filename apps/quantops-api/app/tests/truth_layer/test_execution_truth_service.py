import pytest

from app.services.execution_truth_service import ExecutionTruthService


class DummyV12:
    async def get_execution_fills(self, limit=100):
        return {
            "items": [
                {
                    "fill_id": "f1",
                    "symbol": "BTC",
                    "side": "buy",
                    "qty": 1,
                    "fill_price": 100,
                }
            ]
        }


@pytest.mark.asyncio
async def test_get_recent_fills():
    svc = ExecutionTruthService(DummyV12())

    result = await svc.get_recent_fills()

    assert result["status"] == "ok"
    assert len(result["items"]) == 1
    assert result["items"][0]["fill_id"] == "f1"