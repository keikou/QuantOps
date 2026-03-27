from __future__ import annotations

from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.services.truth_engine import TruthEngine
from ai_hedge_bot.services.position_costing import apply_fill_to_position_state

class TruthEngineAdapter:
    """
    pytest 用の薄い adapter。
    本流の TruthEngine 実装は変更せず、テストが期待する
    apply_fill / apply_mark / get_state / rebuild_from_history を提供する。
    """

    def __init__(self) -> None:
        self.engine = TruthEngine()
        self.engine.ensure_schema()
        self._reset_test_tables()

    def _reset_test_tables(self) -> None:
        tables = [
            "execution_orders",
            "execution_fills",
            "market_prices_latest",
            "market_prices_history",
            "position_snapshots_latest",
            "position_snapshots_history",
            "equity_snapshots",
            "cash_ledger",
            "position_snapshot_versions",
            "execution_state_snapshots",
            "execution_block_reasons",
            "event_store",
        ]
        for table in tables:
            self.engine.store.execute(f"DELETE FROM {table}")
        self.engine.ensure_initial_capital()
        
    def apply_fill(self, fill: dict[str, Any]) -> None:
        now = utc_now_iso()

        qty = float(fill.get("qty", 0.0) or 0.0)
        fee = float(fill.get("fee", 0.0) or 0.0)

        fill_row = {
            "fill_id": fill.get("fill_id"),
            "order_id": fill.get("order_id") or fill.get("fill_id"),
            "client_order_id": fill.get("client_order_id") or fill.get("fill_id"),
            "strategy_id": fill.get("strategy_id") or "paper_runtime",
            "alpha_family": fill.get("alpha_family") or "runtime",
            "run_id": fill.get("run_id") or "test_run",
            "plan_id": fill.get("plan_id") or fill.get("fill_id"),
            "symbol": fill.get("symbol"),
            "side": fill.get("side"),
            "fill_qty": qty,
            #"qty": qty,
            "fill_price": float(fill.get("price", 0.0) or 0.0),
            # テストの fee は絶対値っぽく渡されるので、ここでは fee_bps には無理に変換しない
            "fee_bps": 0.0,
            "price_source": "test",
            "bid": None,
            "ask": None,
            "arrival_mid_price": None,
            "quote_time": now,
            "quote_age_sec": 0.0,
            "fallback_reason": None,
            "created_at": now,
        }

        # idempotency をテストしやすいよう、同一 fill_id があれば重複投入しない
        existing = self.engine.store.fetchone_dict(
            "SELECT fill_id FROM execution_fills WHERE fill_id = ? LIMIT 1",
            [fill_row["fill_id"]],
        )
        if existing:
            return

        self.engine.store.append("execution_fills", fill_row)

        # cash ledger / execution_orders / truth events 更新
        # record_orders_and_fills は fill_price, qty, side を見て cash を更新する
        self.engine.record_orders_and_fills([fill_row], now)

        # fee を絶対額として別建て反映したい場合
        if fee:
            latest_balance = self.engine.latest_cash_balance()
            fee_balance = round(latest_balance - fee, 8)
            self.engine.store.append(
                "cash_ledger",
                {
                    "ledger_id": f"{fill_row['fill_id']}_fee",
                    "event_type": "fee",
                    "ref_id": fill_row["fill_id"],
                    "venue_id": None,
                    "account_id": None,
                    "currency": "USD",
                    "delta_cash": -fee,
                    "balance_after": fee_balance,
                    "event_time": now,
                    "inserted_at": now,
                },
            )

    def apply_mark(self, symbol: str, price: float, ts: int | None = None) -> None:
        now = utc_now_iso()
        self.engine.upsert_market_prices(
            [
                {
                    "symbol": symbol,
                    "bid": price,
                    "ask": price,
                    "mid": price,
                    "last": price,
                    "mark_price": price,
                    "source": "test",
                    "quote_time": now,
                    "quote_age_sec": 0.0,
                    "stale": False,
                    "fallback_reason": None,
                }
            ],
            now,
        )

    def get_state(self) -> dict[str, float]:
        # fills を時間順に replay して、flat 後も realized を保持する
        fills = self.engine.store.fetchall_dict(
            """
            SELECT symbol, side, fill_qty, fill_price, created_at, fill_id
            FROM execution_fills
            ORDER BY created_at ASC, fill_id ASC
            """
        )

        states: dict[str, dict[str, float | None]] = {}

        for fill in fills:
            symbol = str(fill["symbol"])
            side = str(fill.get("side", "") or "").lower()
            qty = float(fill.get("fill_qty", 0.0) or 0.0)
            price = float(fill.get("fill_price", 0.0) or 0.0)

            signed_fill = qty if side == "buy" else -qty

            state = states.setdefault(
                symbol,
                {
                    "signed_qty": 0.0,
                    "avg_entry_price": None,
                    "realized_pnl": 0.0,
                },
            )

            updated_state, _ = apply_fill_to_position_state(
                current_signed_qty=float(state["signed_qty"]),
                current_avg_entry_price=state.get("avg_entry_price"),
                current_realized_pnl=float(state.get("realized_pnl", 0.0) or 0.0),
                fill_signed_qty=signed_fill,
                fill_price=price,
            )
            state.update(updated_state)

        # 最新 mark を読む
        price_rows = self.engine.store.fetchall_dict(
            """
            SELECT symbol, mark_price
            FROM market_prices_latest
            """
        )
        mark_by_symbol = {
            str(row["symbol"]): float(row.get("mark_price", 0.0) or 0.0)
            for row in price_rows
        }

        total_signed_qty = 0.0
        total_abs_qty = 0.0
        weighted_avg_numerator = 0.0
        total_realized = 0.0
        total_unrealized = 0.0

        for symbol, state in states.items():
            signed_qty = float(state.get("signed_qty", 0.0) or 0.0)
            avg_entry_price = state.get("avg_entry_price")
            realized_pnl = float(state.get("realized_pnl", 0.0) or 0.0)

            total_signed_qty += signed_qty
            total_abs_qty += abs(signed_qty)
            total_realized += realized_pnl

            if avg_entry_price is not None and signed_qty != 0.0:
                avg_entry_price = float(avg_entry_price)
                weighted_avg_numerator += abs(signed_qty) * avg_entry_price
                mark_price = float(mark_by_symbol.get(symbol, avg_entry_price))
                total_unrealized += (mark_price - avg_entry_price) * signed_qty

        weighted_avg = weighted_avg_numerator / total_abs_qty if total_abs_qty > 0 else 0.0

        cash_balance = self.engine.latest_cash_balance()
        total_equity = cash_balance
        for symbol, state in states.items():
            signed_qty = float(state.get("signed_qty", 0.0) or 0.0)
            if signed_qty != 0.0:
                mark_price = float(mark_by_symbol.get(symbol, 0.0))
                total_equity += signed_qty * mark_price

        return {
            "position_qty": total_signed_qty,
            "avg_price": weighted_avg,
            "realized_pnl": total_realized,
            "unrealized_pnl": total_unrealized,
            "total_equity": total_equity,
        }

    def rebuild_from_history(
        self,
        fills: list[dict[str, Any]],
        marks: list[tuple[str, float, int]],
    ) -> dict[str, float]:
        fresh = TruthEngineAdapter()
        for fill in fills:
            fresh.apply_fill(fill)
        for symbol, price, ts in marks:
            fresh.apply_mark(symbol, price, ts)
        return fresh.get_state()