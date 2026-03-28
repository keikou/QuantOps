from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.data.collectors.binance_public_client import BinancePublicClient

from ai_hedge_bot.services.cash_engine import compute_fill_cash_delta
from ai_hedge_bot.services.equity_engine import compute_equity_snapshot_row
from ai_hedge_bot.services.event_store import append_truth_event
from ai_hedge_bot.services.position_costing import apply_fill_to_position_state
from ai_hedge_bot.services.snapshot_engine import build_position_snapshot_rows


def _fill_signed_qty(fill: dict[str, Any]) -> float:
    raw = fill.get("signed_qty")
    if raw is None:
        raw = fill.get("qty", fill.get("fill_qty", 0.0))
    qty = float(raw or 0.0)
    side = str(fill.get("side", "") or "").lower()
    if qty == 0.0:
        return 0.0
    if side == "sell":
        return -abs(qty)
    if side == "buy":
        return abs(qty)
    return qty


def _position_state_key(
    symbol: str,
    strategy_id: str | None,
    alpha_family: str | None,
    venue_id: str | None = None,
    account_id: str | None = None,
) -> tuple[str, str, str, str, str]:
    return (
        str(symbol),
        str(strategy_id or "paper_runtime"),
        str(alpha_family or "runtime"),
        str(venue_id or ""),
        str(account_id or ""),
    )


@dataclass
class TruthEngine:
    initial_capital: float = 100000.0
    store: Any | None = None

    def __post_init__(self) -> None:
        self.store = self.store or CONTAINER.runtime_store
        self.quote_client = BinancePublicClient()
        self.last_record_orders_and_fills_metrics: dict[str, Any] = {}
        self.last_rebuild_positions_metrics: dict[str, Any] = {}
        self.last_compute_equity_snapshot_metrics: dict[str, Any] = {}
        self._last_rebuild_positions_fill_watermark: tuple[str | None, str | None, bool] | None = None
        self._last_rebuild_positions_fills: list[dict[str, Any]] | None = None
        self._last_position_rollup_as_of: str | None = None
        self._last_position_rollup: dict[str, float] | None = None

    def ensure_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS execution_orders (
                order_id VARCHAR,
                plan_id VARCHAR,
                parent_order_id VARCHAR,
                client_order_id VARCHAR,
                strategy_id VARCHAR,
                alpha_family VARCHAR,
                symbol VARCHAR,
                side VARCHAR,
                order_type VARCHAR,
                qty DOUBLE,
                limit_price DOUBLE,
                venue VARCHAR,
                route VARCHAR,
                algo VARCHAR,
                submit_time TIMESTAMP,
                status VARCHAR,
                source VARCHAR,
                metadata_json VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS execution_fills (
                fill_id VARCHAR,
                order_id VARCHAR,
                client_order_id VARCHAR,
                strategy_id VARCHAR,
                alpha_family VARCHAR,
                run_id VARCHAR,
                plan_id VARCHAR,
                symbol VARCHAR,
                side VARCHAR,
                fill_qty DOUBLE,
                qty DOUBLE,
                fill_price DOUBLE,
                fee_bps DOUBLE,
                price_source VARCHAR,
                bid DOUBLE,
                ask DOUBLE,
                arrival_mid_price DOUBLE,
                quote_time TIMESTAMP,
                quote_age_sec DOUBLE,
                fallback_reason VARCHAR,
                created_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS market_prices_latest (
                symbol VARCHAR,
                bid DOUBLE,
                ask DOUBLE,
                mid DOUBLE,
                last DOUBLE,
                mark_price DOUBLE,
                source VARCHAR,
                price_time TIMESTAMP,
                quote_age_sec DOUBLE,
                stale BOOLEAN,
                fallback_reason VARCHAR,
                updated_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS market_prices_history (
                symbol VARCHAR,
                bid DOUBLE,
                ask DOUBLE,
                mid DOUBLE,
                last DOUBLE,
                mark_price DOUBLE,
                source VARCHAR,
                price_time TIMESTAMP,
                quote_age_sec DOUBLE,
                stale BOOLEAN,
                fallback_reason VARCHAR,
                inserted_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS position_snapshots_latest (
                snapshot_version VARCHAR,
                symbol VARCHAR,
                strategy_id VARCHAR,
                alpha_family VARCHAR,
                venue_id VARCHAR,
                account_id VARCHAR,
                reporting_currency VARCHAR,
                signed_qty DOUBLE,
                abs_qty DOUBLE,
                side VARCHAR,
                avg_entry_price DOUBLE,
                mark_price DOUBLE,
                market_value DOUBLE,
                unrealized_pnl DOUBLE,
                realized_pnl DOUBLE,
                exposure_notional DOUBLE,
                price_source VARCHAR,
                quote_time TIMESTAMP,
                quote_age_sec DOUBLE,
                stale BOOLEAN,
                updated_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS position_snapshots_history (
                snapshot_version VARCHAR,
                snapshot_time TIMESTAMP,
                symbol VARCHAR,
                strategy_id VARCHAR,
                alpha_family VARCHAR,
                venue_id VARCHAR,
                account_id VARCHAR,
                reporting_currency VARCHAR,
                signed_qty DOUBLE,
                abs_qty DOUBLE,
                side VARCHAR,
                avg_entry_price DOUBLE,
                mark_price DOUBLE,
                market_value DOUBLE,
                unrealized_pnl DOUBLE,
                realized_pnl DOUBLE,
                exposure_notional DOUBLE,
                price_source VARCHAR,
                quote_time TIMESTAMP,
                quote_age_sec DOUBLE,
                stale BOOLEAN
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS equity_snapshots (
                snapshot_time TIMESTAMP,
                venue_id VARCHAR,
                account_id VARCHAR,
                reporting_currency VARCHAR,
                cash_balance DOUBLE,
                free_cash DOUBLE,
                used_margin DOUBLE,
                gross_exposure DOUBLE,
                net_exposure DOUBLE,
                long_exposure DOUBLE,
                short_exposure DOUBLE,
                market_value DOUBLE,
                unrealized_pnl DOUBLE,
                realized_pnl DOUBLE,
                fees_paid DOUBLE,
                total_equity DOUBLE,
                drawdown DOUBLE,
                peak_equity DOUBLE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cash_ledger (
                ledger_id VARCHAR,
                event_type VARCHAR,
                ref_id VARCHAR,
                venue_id VARCHAR,
                account_id VARCHAR,
                currency VARCHAR,
                delta_cash DOUBLE,
                balance_after DOUBLE,
                event_time TIMESTAMP,
                inserted_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS execution_state_snapshots (
                as_of TIMESTAMP,
                trading_state VARCHAR,
                execution_state VARCHAR,
                reason VARCHAR,
                planner_age_sec DOUBLE,
                execution_age_sec DOUBLE,
                last_fill_age_sec DOUBLE,
                open_order_count INTEGER,
                active_plan_count INTEGER,
                expired_plan_count INTEGER,
                latest_plan_id VARCHAR,
                latest_order_id VARCHAR,
                latest_fill_id VARCHAR
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS execution_block_reasons (
                as_of TIMESTAMP,
                code VARCHAR,
                severity VARCHAR,
                message VARCHAR,
                details_json VARCHAR
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS position_snapshot_versions (
                version_id VARCHAR,
                build_status VARCHAR,
                snapshot_time TIMESTAMP,
                row_count INTEGER,
                fills_scanned INTEGER,
                build_duration_ms DOUBLE,
                created_at TIMESTAMP,
                activated_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS truth_engine_state (
                state_key VARCHAR,
                state_value VARCHAR,
                updated_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS event_store (
                event_id VARCHAR,
                event_type VARCHAR,
                aggregate_type VARCHAR,
                aggregate_id VARCHAR,
                venue_id VARCHAR,
                account_id VARCHAR,
                instrument_id VARCHAR,
                event_time TIMESTAMP,
                payload_json VARCHAR,
                version INTEGER
            )
            """,
        ]
        for stmt in statements:
            self.store.execute(stmt)
        alter_statements = [
            "ALTER TABLE execution_orders ADD COLUMN plan_id VARCHAR",
            "ALTER TABLE execution_orders ADD COLUMN parent_order_id VARCHAR",
            "ALTER TABLE execution_orders ADD COLUMN venue VARCHAR",
            "ALTER TABLE execution_orders ADD COLUMN route VARCHAR",
            "ALTER TABLE execution_orders ADD COLUMN algo VARCHAR",
            "ALTER TABLE execution_orders ADD COLUMN submit_time TIMESTAMP",
            "ALTER TABLE execution_orders ADD COLUMN metadata_json VARCHAR",
            "ALTER TABLE execution_plans ADD COLUMN metadata_json VARCHAR",
            "ALTER TABLE execution_plans ADD COLUMN slice_count INTEGER",
            "ALTER TABLE execution_plans ADD COLUMN expire_seconds INTEGER",
            "ALTER TABLE execution_plans ADD COLUMN route VARCHAR",
            "ALTER TABLE execution_plans ADD COLUMN algo VARCHAR",
            "ALTER TABLE execution_fills ADD COLUMN order_id VARCHAR",
            "ALTER TABLE execution_fills ADD COLUMN client_order_id VARCHAR",
            "ALTER TABLE execution_fills ADD COLUMN strategy_id VARCHAR",
            "ALTER TABLE execution_fills ADD COLUMN alpha_family VARCHAR",
            "ALTER TABLE execution_fills ADD COLUMN price_source VARCHAR",
            "ALTER TABLE execution_fills ADD COLUMN bid DOUBLE",
            "ALTER TABLE execution_fills ADD COLUMN ask DOUBLE",
            "ALTER TABLE execution_fills ADD COLUMN arrival_mid_price DOUBLE",
            "ALTER TABLE execution_fills ADD COLUMN quote_time TIMESTAMP",
            "ALTER TABLE execution_fills ADD COLUMN quote_age_sec DOUBLE",
            "ALTER TABLE execution_fills ADD COLUMN fallback_reason VARCHAR",
            "ALTER TABLE market_prices_latest ADD COLUMN quote_age_sec DOUBLE",
            "ALTER TABLE market_prices_latest ADD COLUMN stale BOOLEAN",
            "ALTER TABLE market_prices_latest ADD COLUMN fallback_reason VARCHAR",
            "ALTER TABLE market_prices_history ADD COLUMN quote_age_sec DOUBLE",
            "ALTER TABLE market_prices_history ADD COLUMN stale BOOLEAN",
            "ALTER TABLE market_prices_history ADD COLUMN fallback_reason VARCHAR",
            "ALTER TABLE position_snapshots_latest ADD COLUMN snapshot_version VARCHAR",
            "ALTER TABLE position_snapshots_latest ADD COLUMN price_source VARCHAR",
            "ALTER TABLE position_snapshots_latest ADD COLUMN quote_time TIMESTAMP",
            "ALTER TABLE position_snapshots_latest ADD COLUMN quote_age_sec DOUBLE",
            "ALTER TABLE position_snapshots_latest ADD COLUMN stale BOOLEAN",
            "ALTER TABLE position_snapshots_latest ADD COLUMN venue_id VARCHAR",
            "ALTER TABLE position_snapshots_latest ADD COLUMN account_id VARCHAR",
            "ALTER TABLE position_snapshots_latest ADD COLUMN reporting_currency VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN snapshot_version VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN price_source VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN quote_time TIMESTAMP",
            "ALTER TABLE position_snapshots_history ADD COLUMN quote_age_sec DOUBLE",
            "ALTER TABLE position_snapshots_history ADD COLUMN stale BOOLEAN",
            "ALTER TABLE position_snapshots_history ADD COLUMN venue_id VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN account_id VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN reporting_currency VARCHAR",
            "ALTER TABLE equity_snapshots ADD COLUMN venue_id VARCHAR",
            "ALTER TABLE equity_snapshots ADD COLUMN account_id VARCHAR",
            "ALTER TABLE equity_snapshots ADD COLUMN reporting_currency VARCHAR",
            "ALTER TABLE equity_snapshots ADD COLUMN free_cash DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN used_margin DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN fees_paid DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN collateral_equity DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN available_margin DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN margin_utilization DOUBLE",
            "ALTER TABLE cash_ledger ADD COLUMN venue_id VARCHAR",
            "ALTER TABLE cash_ledger ADD COLUMN account_id VARCHAR",
            "ALTER TABLE cash_ledger ADD COLUMN currency VARCHAR",
            "ALTER TABLE event_store ADD COLUMN venue_id VARCHAR",
            "ALTER TABLE event_store ADD COLUMN account_id VARCHAR",
            "ALTER TABLE event_store ADD COLUMN instrument_id VARCHAR",
            "ALTER TABLE event_store ADD COLUMN version INTEGER",
        ]
        for stmt in alter_statements:
            try:
                self.store.execute(stmt)
            except Exception:
                pass
        self.ensure_initial_capital()

    def _quote_age_sec(self, quote_time: str | None, as_of: str) -> float:
        try:
            quote_ts = str(quote_time or as_of).replace("Z", "+00:00")
            as_of_ts = str(as_of).replace("Z", "+00:00")
            delta = __import__("datetime").datetime.fromisoformat(as_of_ts) - __import__("datetime").datetime.fromisoformat(quote_ts)
            return max(0.0, delta.total_seconds())
        except Exception:
            return 0.0

    def _get_state_value(self, key: str) -> str | None:
        row = self.store.fetchone_dict(
            """
            SELECT state_value
            FROM truth_engine_state
            WHERE state_key = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [key],
        )
        value = (row or {}).get("state_value")
        return str(value) if value is not None else None

    def _set_state_value(self, key: str, value: str, as_of: str, conn=None) -> None:
        self.store.execute("DELETE FROM truth_engine_state WHERE state_key = ?", [key], conn=conn)
        self.store.append(
            "truth_engine_state",
            {
                "state_key": key,
                "state_value": value,
                "updated_at": as_of,
            },
            conn=conn,
        )

    def _get_fill_watermark(self, key: str) -> tuple[str | None, str | None]:
        raw = self._get_state_value(key)
        if not raw:
            return None, None
        try:
            created_at, fill_id = raw.split("|", 1)
            return created_at or None, fill_id or None
        except Exception:
            return None, None

    def _set_fill_watermark(self, key: str, fill: dict[str, Any] | None, as_of: str, conn=None) -> None:
        if not fill:
            return
        created_at = str(fill.get("created_at") or as_of)
        fill_id = str(fill.get("fill_id") or "")
        if not fill_id:
            return
        self._set_state_value(key, f"{created_at}|{fill_id}", as_of, conn=conn)

    def _get_equity_state(self) -> dict[str, float] | None:
        raw = self._get_state_value("equity_snapshot_state")
        if not raw:
            return None
        try:
            cash_balance, fees_paid, realized_pnl, peak_equity = raw.split("|", 3)
            return {
                "cash_balance": float(cash_balance or self.initial_capital),
                "fees_paid": float(fees_paid or 0.0),
                "realized_pnl": float(realized_pnl or 0.0),
                "peak_equity": float(peak_equity or self.initial_capital),
            }
        except Exception:
            return None

    def _set_equity_state(self, row: dict[str, Any], as_of: str, conn=None) -> None:
        payload = "|".join(
            [
                str(float(row.get("cash_balance", self.initial_capital) or self.initial_capital)),
                str(float(row.get("fees_paid", 0.0) or 0.0)),
                str(float(row.get("realized_pnl", 0.0) or 0.0)),
                str(float(row.get("peak_equity", self.initial_capital) or self.initial_capital)),
            ]
        )
        self._set_state_value("equity_snapshot_state", payload, as_of, conn=conn)

    def _fetch_new_fills(self, created_at: str | None, fill_id: str | None) -> list[dict[str, Any]]:
        if not created_at or not fill_id:
            return self.store.fetchall_dict(
                """
                SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
                FROM execution_fills
                ORDER BY created_at ASC, fill_id ASC
                """
            )
        return self.store.fetchall_dict(
            """
            SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
            FROM execution_fills
            WHERE created_at > ? OR (created_at = ? AND fill_id > ?)
            ORDER BY created_at ASC, fill_id ASC
            """,
            [created_at, created_at, fill_id],
        )

    def _remember_rebuild_fills(
        self,
        *,
        created_at: str | None,
        fill_id: str | None,
        full_rebuild: bool,
        fills: list[dict[str, Any]],
    ) -> None:
        self._last_rebuild_positions_fill_watermark = (created_at, fill_id, full_rebuild)
        self._last_rebuild_positions_fills = list(fills)

    def _reuse_rebuild_fills(
        self,
        *,
        created_at: str | None,
        fill_id: str | None,
        full_rebuild: bool,
    ) -> list[dict[str, Any]] | None:
        if self._last_rebuild_positions_fill_watermark != (created_at, fill_id, full_rebuild):
            return None
        if self._last_rebuild_positions_fills is None:
            return None
        return list(self._last_rebuild_positions_fills)

    @staticmethod
    def _summarize_positions_for_equity(positions: list[dict[str, Any]]) -> dict[str, float]:
        return {
            "realized_total": round(sum(float(p.get("realized_pnl", 0.0) or 0.0) for p in positions), 8),
            "unrealized": round(sum(float(p.get("unrealized_pnl", 0.0) or 0.0) for p in positions), 8),
            "used_margin": round(sum(float(p.get("avg_entry_price", 0.0) or 0.0) * float(p.get("abs_qty", 0.0) or 0.0) for p in positions), 8),
            "current_long_notional": round(sum(max(0.0, float(p.get("market_value", 0.0) or 0.0)) for p in positions), 8),
            "current_short_notional": round(sum(abs(min(0.0, float(p.get("market_value", 0.0) or 0.0))) for p in positions), 8),
            "market_value": round(sum(float(p.get("market_value", 0.0) or 0.0) for p in positions), 8),
        }

    def _remember_position_rollup(self, as_of: str, positions: list[dict[str, Any]]) -> None:
        self._last_position_rollup_as_of = as_of
        self._last_position_rollup = self._summarize_positions_for_equity(positions)

    def _reuse_position_rollup(self, as_of: str) -> dict[str, float] | None:
        if self._last_position_rollup_as_of != as_of:
            return None
        if self._last_position_rollup is None:
            return None
        return dict(self._last_position_rollup)

    def ensure_initial_capital(self) -> None:
        row = self.store.fetchone_dict("SELECT COUNT(*) AS c FROM cash_ledger")
        if row and int(row.get("c") or 0) > 0:
            return
        now = utc_now_iso()
        self.store.append(
            "cash_ledger",
            {
                "ledger_id": new_cycle_id(),
                "event_type": "initial_capital",
                "ref_id": "seed",
                "venue_id": None,
                "account_id": None,
                "currency": "USD",
                "delta_cash": self.initial_capital,
                "balance_after": self.initial_capital,
                "event_time": now,
                "inserted_at": now,
            },
        )
    def get_latest_market_prices(self, symbols: list[str]) -> dict[str, dict]:
        if not symbols:
            return {}

        placeholders = ",".join(["?"] * len(symbols))

        rows = self.store.fetchall_dict(
            f"""
            SELECT *
            FROM market_prices_latest
            WHERE symbol IN ({placeholders})
            """,
            symbols,
        )

        out: dict[str, dict] = {}
        for row in rows:
            symbol = str(row.get("symbol"))
            out[symbol] = row

        return out

    def latest_cash_balance(self) -> float:
        row = self.store.fetchone_dict(
            """
            SELECT balance_after
            FROM cash_ledger
            ORDER BY event_time DESC, inserted_at DESC
            LIMIT 1
            """
        )
        if not row:
            return self.initial_capital
        return float(row.get("balance_after", self.initial_capital) or self.initial_capital)

    def upsert_market_prices(self, prices: list[dict[str, Any]], as_of: str) -> None:
        symbols = [str(p["symbol"]) for p in prices]
        if symbols:
            placeholders = ",".join(["?"] * len(symbols))
            self.store.execute(f"DELETE FROM market_prices_latest WHERE symbol IN ({placeholders})", symbols)

        latest_rows = []
        history_rows = []
        for p in prices:
            row = {
                "symbol": p["symbol"],
                "bid": p.get("bid"),
                "ask": p.get("ask"),
                "mid": p.get("mid"),
                "last": p.get("last"),
                "mark_price": p["mark_price"],
                "source": p.get("source", "synthetic_quote_fallback"),
                "price_time": p.get("quote_time", as_of),
                "quote_age_sec": float(p.get("quote_age_sec", 0.0) or 0.0),
                "stale": bool(p.get("stale", False)),
                "fallback_reason": p.get("fallback_reason"),
                "updated_at": as_of,
            }
            latest_rows.append(row)
            history_rows.append(
                {
                    **{k: v for k, v in row.items() if k != "updated_at"},
                    "inserted_at": as_of,
                }
            )

        if latest_rows:
            self.store.append("market_prices_latest", latest_rows)
            self.store.append("market_prices_history", history_rows)

    def _compute_cash_balance_from_fills(self, fills: list[dict[str, Any]]) -> tuple[float, float]:
        balance = float(self.initial_capital)
        total_fees = 0.0
        for fill in fills:
            signed_qty = _fill_signed_qty(fill)
            qty = abs(signed_qty)
            price = float(fill.get("fill_price", 0.0) or 0.0)
            fee_bps = float(fill.get("fee_bps", 0.0) or 0.0)
            fee = qty * price * fee_bps / 10000.0
            balance += -(signed_qty * price) - fee
            total_fees += fee
        return round(balance, 8), round(total_fees, 8)

    def record_orders_and_fills(self, fills: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
        orders = []
        ledger_rows = []
        balance = self.latest_cash_balance()

        for fill in fills:
            order_id = fill.get("order_id") or fill.get("plan_id") or new_cycle_id()
            signed_qty = _fill_signed_qty(fill)
            abs_qty = abs(signed_qty)
            price = float(fill.get("fill_price", 0.0) or 0.0)
            fee_bps = float(fill.get("fee_bps", 0.0) or 0.0)

            delta_cash, fee = compute_fill_cash_delta(
                signed_qty=signed_qty,
                fill_price=price,
                fee_bps=fee_bps,
            )
            balance = round(balance + delta_cash, 8)

            side = str(fill.get("side", "buy") or ("buy" if signed_qty >= 0 else "sell")).lower()
            orders.append(
                {
                    "order_id": order_id,
                    "client_order_id": fill.get("client_order_id") or order_id,
                    "strategy_id": fill.get("strategy_id") or fill.get("run_id") or "paper_runtime",
                    "alpha_family": fill.get("alpha_family") or "runtime",
                    "symbol": fill["symbol"],
                    "side": side,
                    "order_type": fill.get("order_type") or "paper_market",
                    "qty": abs_qty,
                    "limit_price": float(fill.get("limit_price", price) or price),
                    "venue": fill.get("venue"),
                    "route": fill.get("route"),
                    "algo": fill.get("algo"),
                    "status": "filled",
                    "source": fill.get("source") or "orchestrator",
                    "metadata_json": json.dumps(fill, ensure_ascii=False),
                    "created_at": as_of,
                    "updated_at": as_of,
                }
            )
            ledger_rows.append(
                {
                    "ledger_id": new_cycle_id(),
                    "event_type": "fill",
                    "ref_id": fill.get("fill_id") or order_id,
                    "venue_id": fill.get("venue_id"),
                    "account_id": fill.get("account_id"),
                    "currency": "USD",
                    "delta_cash": delta_cash,
                    "balance_after": balance,
                    "event_time": as_of,
                    "inserted_at": as_of,
                }
            )

            append_truth_event(
                self.store,
                event_type="fill_recorded",
                aggregate_type="order",
                aggregate_id=str(order_id),
                payload=fill,
                as_of=as_of,
                venue_id=fill.get("venue_id"),
                account_id=fill.get("account_id"),
                instrument_id=fill.get("symbol"),
            )

        if orders:
            self.store.append("execution_orders", orders)
            self.store.append("cash_ledger", ledger_rows)

        self.last_record_orders_and_fills_metrics = {
            "fill_rows": len(fills),
            "order_rows": len(orders),
            "ledger_rows": len(ledger_rows),
        }
        return self.last_record_orders_and_fills_metrics

    def rebuild_positions(self, as_of: str) -> list[dict[str, Any]]:
        started_at = time.perf_counter()

        fills = self.store.fetchall_dict(
            """
            SELECT fill_id, order_id, client_order_id, strategy_id, alpha_family, run_id, plan_id,
                   symbol, side, fill_qty, fill_price, fee_bps, created_at
            FROM execution_fills
            ORDER BY created_at ASC, fill_id ASC
            """
        )
        self._remember_rebuild_fills(
            created_at=None,
            fill_id=None,
            full_rebuild=True,
            fills=fills,
        )

        price_rows = self.store.fetchall_dict(
            """
            SELECT symbol, bid, ask, mid, last, mark_price, source, price_time, quote_age_sec, stale, fallback_reason
            FROM market_prices_latest
            """
        )
        price_by_symbol = {str(r["symbol"]): r for r in price_rows}

        states: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

        for fill in fills:
            symbol = str(fill["symbol"])
            strategy_id = str(fill.get("strategy_id") or fill.get("run_id") or "paper_runtime")
            alpha_family = str(fill.get("alpha_family") or "runtime")
            venue_id = fill.get("venue_id")
            account_id = fill.get("account_id")
            key = _position_state_key(symbol, strategy_id, alpha_family, venue_id, account_id)

            state = states.setdefault(
                key,
                {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "alpha_family": alpha_family,
                    "venue_id": venue_id,
                    "account_id": account_id,
                    "reporting_currency": "USD",
                    "signed_qty": 0.0,
                    "avg_entry_price": None,
                    "realized_pnl": 0.0,
                },
            )

            signed_fill = _fill_signed_qty(fill)
            price = float(fill.get("fill_price", 0.0) or 0.0)

            updated_state, _ = apply_fill_to_position_state(
                current_signed_qty=float(state["signed_qty"]),
                current_avg_entry_price=state.get("avg_entry_price"),
                current_realized_pnl=float(state.get("realized_pnl", 0.0) or 0.0),
                fill_signed_qty=signed_fill,
                fill_price=price,
            )
            state.update(updated_state)

        snapshot_version = new_cycle_id()
        latest_rows = build_position_snapshot_rows(
            states=states,
            price_by_symbol=price_by_symbol,
            as_of=as_of,
            snapshot_version=snapshot_version,
        )

        self.store.execute("DELETE FROM position_snapshots_latest")
        if latest_rows:
            self.store.append("position_snapshots_latest", latest_rows)
            history_rows = [
                {
                    "snapshot_version": row["snapshot_version"],
                    "snapshot_time": as_of,
                    "symbol": row["symbol"],
                    "strategy_id": row["strategy_id"],
                    "alpha_family": row["alpha_family"],
                    "venue_id": row.get("venue_id"),
                    "account_id": row.get("account_id"),
                    "reporting_currency": row.get("reporting_currency", "USD"),
                    "signed_qty": row["signed_qty"],
                    "abs_qty": row["abs_qty"],
                    "side": row["side"],
                    "avg_entry_price": row["avg_entry_price"],
                    "mark_price": row["mark_price"],
                    "market_value": row["market_value"],
                    "unrealized_pnl": row["unrealized_pnl"],
                    "realized_pnl": row["realized_pnl"],
                    "exposure_notional": row["exposure_notional"],
                    "price_source": row["price_source"],
                    "quote_time": row["quote_time"],
                    "quote_age_sec": row["quote_age_sec"],
                    "stale": row["stale"],
                }
                for row in latest_rows
            ]
            self.store.append("position_snapshots_history", history_rows)

        self.store.append(
            "position_snapshot_versions",
            {
                "version_id": snapshot_version,
                "build_status": "active",
                "snapshot_time": as_of,
                "row_count": len(latest_rows),
                "fills_scanned": len(fills),
                "build_duration_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
                "created_at": as_of,
                "activated_at": as_of,
            },
        )

        append_truth_event(
            self.store,
            event_type="positions_rebuilt",
            aggregate_type="portfolio",
            aggregate_id="global_positions",
            payload={"row_count": len(latest_rows), "snapshot_version": snapshot_version},
            as_of=as_of,
        )

        self.last_rebuild_positions_metrics = {
            "snapshot_version": snapshot_version,
            "fills_scanned": len(fills),
            "position_rows": len(latest_rows),
            "build_duration_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
            "rebuild_mode": "full",
        }
        self._remember_position_rollup(as_of, latest_rows)
        return latest_rows

    def compute_equity_snapshot(self, positions: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
        started_at = time.perf_counter()
        watermark_created_at, watermark_fill_id = self._get_fill_watermark("equity_last_fill")
        previous = self._get_equity_state()
        existing_snapshot = self.store.fetchone_dict(
            """
            SELECT snapshot_time, cash_balance, fees_paid, realized_pnl, peak_equity
            FROM equity_snapshots
            ORDER BY snapshot_time DESC
            LIMIT 1
            """
        )
        if existing_snapshot is None:
            previous = None
        if previous is None:
            previous = existing_snapshot
        full_rebuild_reason = None
        if previous is None:
            full_rebuild_reason = "missing_previous_snapshot"
        elif not watermark_created_at or not watermark_fill_id:
            full_rebuild_reason = "missing_fill_watermark"
        full_rebuild = full_rebuild_reason is not None

        fills = self._reuse_rebuild_fills(
            created_at=watermark_created_at,
            fill_id=watermark_fill_id,
            full_rebuild=full_rebuild,
        )
        if fills is None:
            fills = (
                self._fetch_new_fills(watermark_created_at, watermark_fill_id)
                if not full_rebuild
                else self.store.fetchall_dict(
                    """
                    SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
                    FROM execution_fills
                    ORDER BY created_at ASC, fill_id ASC
                    """
                )
            )

        if full_rebuild:
            cash_balance, fees_paid = self._compute_cash_balance_from_fills(fills)
        else:
            prev_cash = float((previous or {}).get("cash_balance", self.initial_capital) or self.initial_capital)
            prev_fees = float((previous or {}).get("fees_paid", 0.0) or 0.0)
            if fills:
                delta_cash_balance, delta_fees = self._compute_cash_balance_from_fills(fills)
                delta_cash = round(delta_cash_balance - self.initial_capital, 8)
                cash_balance = round(prev_cash + delta_cash, 8)
                fees_paid = round(prev_fees + delta_fees, 8)
            else:
                cash_balance = round(prev_cash, 8)
                fees_paid = round(prev_fees, 8)

        previous_peak = float((previous or {}).get("peak_equity", self.initial_capital) or self.initial_capital)
        base_row = compute_equity_snapshot_row(
            cash_balance=cash_balance,
            positions=positions,
            previous_peak_equity=previous_peak,
            reporting_currency="USD",
            as_of=as_of,
        )
        position_rollup = self._reuse_position_rollup(as_of)
        position_rollup_source = "cached" if position_rollup is not None else "computed"
        if position_rollup is None:
            position_rollup = self._summarize_positions_for_equity(positions)

        used_margin = float(position_rollup["used_margin"])
        current_long_notional = float(position_rollup["current_long_notional"])
        current_short_notional = float(position_rollup["current_short_notional"])
        market_value = float(position_rollup["market_value"])
        unrealized = float(base_row["unrealized_pnl"])
        total_equity = round(cash_balance + market_value, 8)
        collateral_equity = round(total_equity - unrealized, 8)
        free_cash = round(max(collateral_equity - used_margin, 0.0), 8)
        available_margin = round(max(total_equity - used_margin, 0.0), 8)
        margin_utilization = round((used_margin / max(collateral_equity, 1e-9)) if collateral_equity > 0 else 0.0, 8)
        equity_denom = max(abs(total_equity), 1e-9)

        full_row = {
            "snapshot_time": base_row["snapshot_time"],
            "venue_id": base_row.get("venue_id"),
            "account_id": base_row.get("account_id"),
            "reporting_currency": base_row.get("reporting_currency", "USD"),
            "cash_balance": round(cash_balance, 8),
            "free_cash": free_cash,
            "used_margin": round(used_margin, 8),
            "collateral_equity": collateral_equity,
            "available_margin": available_margin,
            "margin_utilization": margin_utilization,
            "gross_exposure": round((current_long_notional + current_short_notional) / equity_denom, 8) if positions else 0.0,
            "net_exposure": round(market_value / equity_denom, 8) if positions else 0.0,
            "long_exposure": round(current_long_notional / equity_denom, 8) if positions else 0.0,
            "short_exposure": round(current_short_notional / equity_denom, 8) if positions else 0.0,
            "market_value": base_row["market_value"],
            "unrealized_pnl": base_row["unrealized_pnl"],
            "realized_pnl": float(position_rollup["realized_total"]),
            "fees_paid": round(fees_paid, 8),
            "total_equity": total_equity,
            "drawdown": base_row["drawdown"],
            "peak_equity": base_row["peak_equity"],
        }

        with self.store._session() as conn:
            self.store.append("equity_snapshots", full_row, conn=conn)
            self._set_fill_watermark("equity_last_fill", fills[-1] if fills else None, as_of, conn=conn)
            self._set_equity_state(full_row, as_of, conn=conn)
            try:
                conn.commit()
            except Exception:
                pass

        append_truth_event(
            self.store,
            event_type="equity_snapshot_created",
            aggregate_type="portfolio",
            aggregate_id="global_equity",
            payload=full_row,
            as_of=as_of,
        )

        self.last_compute_equity_snapshot_metrics = {
            "fills_scanned": len(fills),
            "new_fills_applied": len(fills),
            "position_rows": len(positions),
            "build_duration_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
            "rebuild_mode": "full" if full_rebuild else "incremental",
            "full_rebuild_reason": full_rebuild_reason,
            "position_rollup_source": position_rollup_source,
        }
        return full_row

    def synthesize_prices(
        self,
        decisions: list[dict[str, Any]],
        created_at: str,
        mode: str,
    ) -> list[dict[str, Any]]:
        symbols = [str(decision["symbol"]) for decision in decisions]
        quotes = {
            quote.symbol: quote.to_dict()
            for quote in self.quote_client.fetch_best_bid_ask_many(symbols)
        }
        prices: list[dict[str, Any]] = []
        for idx, decision in enumerate(decisions):
            symbol = str(decision["symbol"])
            quote = quotes.get(symbol)
            if quote is None:
                base_price = 100.0 + idx * 5.0
                spread_bps = 2.0 if mode == "paper" else 4.0
                bid = round(base_price * (1.0 - spread_bps / 20000.0), 8)
                ask = round(base_price * (1.0 + spread_bps / 20000.0), 8)
                mid = round((bid + ask) / 2.0, 8)
                quote = {
                    "symbol": symbol,
                    "bid": bid,
                    "ask": ask,
                    "mid": mid,
                    "last": mid,
                    "mark_price": mid,
                    "source": f"{mode}_synthetic_quote_fallback",
                    "quote_time": created_at,
                    "stale": True,
                    "fallback_reason": "missing_quote",
                    "quote_age_sec": 0.0,
                }
            prices.append(quote)
        return prices
