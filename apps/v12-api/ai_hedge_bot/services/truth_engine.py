from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.data.collectors.binance_public_client import BinancePublicClient
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id


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


def _position_state_key(symbol: str, strategy_id: str | None, alpha_family: str | None) -> tuple[str, str, str]:
    return (
        str(symbol),
        str(strategy_id or "paper_runtime"),
        str(alpha_family or "runtime"),
    )


@dataclass
class TruthEngine:
    initial_capital: float = 100000.0

    def __post_init__(self) -> None:
        self.quote_client = BinancePublicClient()
        self.last_record_orders_and_fills_metrics: dict[str, Any] = {}
        self.last_rebuild_positions_metrics: dict[str, Any] = {}
        self.last_compute_equity_snapshot_metrics: dict[str, Any] = {}

    def ensure_schema(self) -> None:
        store = CONTAINER.runtime_store
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
        ]
        for stmt in statements:
            store.execute(stmt)
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
            "ALTER TABLE equity_snapshots ADD COLUMN free_cash DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN used_margin DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN fees_paid DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN collateral_equity DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN available_margin DOUBLE",
            "ALTER TABLE equity_snapshots ADD COLUMN margin_utilization DOUBLE",
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
            "ALTER TABLE position_snapshots_history ADD COLUMN snapshot_version VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN price_source VARCHAR",
            "ALTER TABLE position_snapshots_history ADD COLUMN quote_time TIMESTAMP",
            "ALTER TABLE position_snapshots_history ADD COLUMN quote_age_sec DOUBLE",
            "ALTER TABLE position_snapshots_history ADD COLUMN stale BOOLEAN",
        ]
        for stmt in alter_statements:
            try:
                store.execute(stmt)
            except Exception:
                pass
        self.ensure_initial_capital()

    def _quote_age_sec(self, quote_time: str | None, as_of: str) -> float:
        try:
            quote_ts = str(quote_time or as_of).replace('Z', '+00:00')
            as_of_ts = str(as_of).replace('Z', '+00:00')
            return max(0.0, (__import__('datetime').datetime.fromisoformat(as_of_ts) - __import__('datetime').datetime.fromisoformat(quote_ts)).total_seconds())
        except Exception:
            return 0.0

    def _get_state_value(self, key: str) -> str | None:
        row = CONTAINER.runtime_store.fetchone_dict(
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
        store = CONTAINER.runtime_store
        store.execute("DELETE FROM truth_engine_state WHERE state_key = ?", [key], conn=conn)
        store.append(
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

    def _active_position_snapshot_version(self) -> str | None:
        row = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT version_id
            FROM position_snapshot_versions
            WHERE build_status = 'active'
            ORDER BY activated_at DESC, created_at DESC
            LIMIT 1
            """
        )
        version_id = str((row or {}).get("version_id") or "")
        return version_id or None

    def _fetch_active_position_rows(self) -> list[dict[str, Any]]:
        store = CONTAINER.runtime_store
        active_version = self._active_position_snapshot_version()
        if active_version:
            return store.fetchall_dict(
                """
                SELECT symbol, strategy_id, alpha_family, signed_qty, abs_qty, side, avg_entry_price,
                       mark_price, market_value, unrealized_pnl, realized_pnl, exposure_notional,
                       price_source, quote_time, quote_age_sec, stale, updated_at
                FROM position_snapshots_latest
                WHERE snapshot_version = ?
                ORDER BY exposure_notional DESC, symbol ASC
                """,
                [active_version],
            )
        return store.fetchall_dict(
            """
            SELECT symbol, strategy_id, alpha_family, signed_qty, abs_qty, side, avg_entry_price,
                   mark_price, market_value, unrealized_pnl, realized_pnl, exposure_notional,
                   price_source, quote_time, quote_age_sec, stale, updated_at
            FROM position_snapshots_latest
            ORDER BY exposure_notional DESC, symbol ASC
            """
        )

    def _fetch_new_fills(self, created_at: str | None, fill_id: str | None) -> list[dict[str, Any]]:
        store = CONTAINER.runtime_store
        if not created_at or not fill_id:
            return store.fetchall_dict(
                """
                SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
                FROM execution_fills
                ORDER BY created_at ASC, fill_id ASC
                """
            )
        return store.fetchall_dict(
            """
            SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
            FROM execution_fills
            WHERE created_at > ? OR (created_at = ? AND fill_id > ?)
            ORDER BY created_at ASC, fill_id ASC
            """,
            [created_at, created_at, fill_id],
        )

    def get_latest_market_prices(self, symbols: list[str] | None = None) -> dict[str, dict[str, Any]]:
        store = CONTAINER.runtime_store
        rows = []
        if symbols:
            placeholders = ','.join(['?'] * len(symbols))
            rows = store.fetchall_dict(f"""
                SELECT symbol, bid, ask, mid, last, mark_price, source, price_time, quote_age_sec, stale, fallback_reason
                FROM market_prices_latest
                WHERE symbol IN ({placeholders})
            """, symbols)
        else:
            rows = store.fetchall_dict("""
                SELECT symbol, bid, ask, mid, last, mark_price, source, price_time, quote_age_sec, stale, fallback_reason
                FROM market_prices_latest
            """)
        return {str(row['symbol']): row for row in rows}

    def ensure_initial_capital(self) -> None:
        store = CONTAINER.runtime_store
        row = store.fetchone_dict("SELECT COUNT(*) AS c FROM cash_ledger")
        if row and int(row.get("c") or 0) > 0:
            return
        now = utc_now_iso()
        store.append(
            "cash_ledger",
            {
                "ledger_id": new_cycle_id(),
                "event_type": "initial_capital",
                "ref_id": "seed",
                "delta_cash": self.initial_capital,
                "balance_after": self.initial_capital,
                "event_time": now,
                "inserted_at": now,
            },
        )

    def upsert_market_prices(self, prices: list[dict[str, Any]], as_of: str) -> None:
        store = CONTAINER.runtime_store
        symbols = [str(p["symbol"]) for p in prices]
        if symbols:
            placeholders = ",".join(["?"] * len(symbols))
            store.execute(f"DELETE FROM market_prices_latest WHERE symbol IN ({placeholders})", symbols)
        latest_rows = []
        history_rows = []
        for p in prices:
            quote_time = p.get("quote_time") or as_of
            quote_age_sec = float(p.get("quote_age_sec", self._quote_age_sec(quote_time, as_of)) or 0.0)
            stale = bool(p.get("stale", quote_age_sec > 30.0))
            row = {
                "symbol": p["symbol"],
                "bid": p["bid"],
                "ask": p["ask"],
                "mid": p["mid"],
                "last": p["last"],
                "mark_price": p["mark_price"],
                "source": p.get("source", "synthetic_quote_fallback"),
                "price_time": quote_time,
                "quote_age_sec": quote_age_sec,
                "stale": stale,
                "fallback_reason": p.get("fallback_reason"),
                "updated_at": as_of,
            }
            latest_rows.append(row)
            history_rows.append({
                'symbol': row['symbol'],
                'bid': row['bid'],
                'ask': row['ask'],
                'mid': row['mid'],
                'last': row['last'],
                'mark_price': row['mark_price'],
                'source': row['source'],
                'price_time': row['price_time'],
                'quote_age_sec': row['quote_age_sec'],
                'stale': row['stale'],
                'fallback_reason': row['fallback_reason'],
                'inserted_at': as_of,
            })
        if latest_rows:
            store.append("market_prices_latest", latest_rows)
            store.append("market_prices_history", history_rows)

    def record_orders_and_fills(self, fills: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
        store = CONTAINER.runtime_store
        orders = []
        ledger_rows = []
        balance = self.latest_cash_balance()
        for fill in fills:
            order_id = fill.get("order_id") or fill.get("plan_id") or new_cycle_id()
            signed_qty = _fill_signed_qty(fill)
            qty = abs(signed_qty)
            price = float(fill.get("fill_price", 0.0) or 0.0)
            fee_bps = float(fill.get("fee_bps", 0.0) or 0.0)
            fee = round(qty * price * fee_bps / 10000.0, 8)
            side = str(fill.get("side", "buy") or ("buy" if signed_qty >= 0 else "sell")).lower()
            delta_cash = round(-(signed_qty * price) - fee, 8)
            balance = round(balance + delta_cash, 8)
            orders.append(
                {
                    "order_id": order_id,
                    "client_order_id": fill.get("client_order_id") or order_id,
                    "strategy_id": fill.get("strategy_id") or fill.get("run_id") or "paper_runtime",
                    "alpha_family": fill.get("alpha_family") or "runtime",
                    "symbol": fill["symbol"],
                    "side": side,
                    "order_type": fill.get("order_type") or "paper_market",
                    "qty": qty,
                    "limit_price": float(fill.get("limit_price", price) or price),
                    "status": "filled",
                    "source": fill.get("source") or "orchestrator",
                    "created_at": as_of,
                    "updated_at": as_of,
                }
            )
            ledger_rows.append(
                {
                    "ledger_id": new_cycle_id(),
                    "event_type": "fill",
                    "ref_id": fill.get("fill_id") or order_id,
                    "delta_cash": delta_cash,
                    "balance_after": balance,
                    "event_time": as_of,
                    "inserted_at": as_of,
                }
            )
        if orders:
            store.append("execution_orders", orders)
            store.append("cash_ledger", ledger_rows)
        self.last_record_orders_and_fills_metrics = {
            "fill_rows": len(fills),
            "order_rows": len(orders),
            "ledger_rows": len(ledger_rows),
        }
        return self.last_record_orders_and_fills_metrics

    def latest_cash_balance(self) -> float:
        row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT balance_after FROM cash_ledger ORDER BY event_time DESC, inserted_at DESC LIMIT 1"
        )
        if not row:
            return self.initial_capital
        return float(row.get("balance_after", self.initial_capital) or self.initial_capital)

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

    def _build_position_states_from_fills(self, fills: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], float, float]:
        states: dict[str, dict[str, Any]] = {}
        total_realized = 0.0
        total_fees = 0.0
        for fill in fills:
            realized, fees = self._apply_fill_to_position_states(states, fill)
            total_realized += realized
            total_fees += fees
        return states, round(total_realized, 8), round(total_fees, 8)

    def _apply_fill_to_position_states(self, states: dict[tuple[str, str, str], dict[str, Any]], fill: dict[str, Any]) -> tuple[float, float]:
            symbol = str(fill["symbol"])
            strategy_id = str(fill.get("strategy_id") or fill.get("run_id") or "paper_runtime")
            alpha_family = str(fill.get("alpha_family") or "runtime")
            state = states.setdefault(
                _position_state_key(symbol, strategy_id, alpha_family),
                {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "alpha_family": alpha_family,
                    "signed_qty": 0.0,
                    "avg_entry_price": None,
                    "realized_pnl": 0.0,
                },
            )
            signed_fill = _fill_signed_qty(fill)
            qty = abs(signed_fill)
            price = float(fill.get("fill_price", 0.0) or 0.0)
            fee_bps = float(fill.get("fee_bps", 0.0) or 0.0)
            total_fees = qty * price * fee_bps / 10000.0
            current_qty = float(state["signed_qty"])
            avg = state["avg_entry_price"]
            total_realized = 0.0
            if current_qty == 0.0 or avg is None:
                state["signed_qty"] = signed_fill
                state["avg_entry_price"] = price if signed_fill != 0 else None
                return total_realized, total_fees
            if current_qty * signed_fill > 0:
                new_qty = current_qty + signed_fill
                state["avg_entry_price"] = ((abs(current_qty) * float(avg)) + (abs(signed_fill) * price)) / max(abs(new_qty), 1e-12)
                state["signed_qty"] = new_qty
                return total_realized, total_fees
            close_qty = min(abs(current_qty), abs(signed_fill))
            if current_qty > 0:
                realized = (price - float(avg)) * close_qty
            else:
                realized = (float(avg) - price) * close_qty
            state["realized_pnl"] += realized
            total_realized += realized
            new_qty = current_qty + signed_fill
            if abs(new_qty) < 1e-12:
                state["signed_qty"] = 0.0
                state["avg_entry_price"] = None
            elif current_qty * new_qty > 0:
                state["signed_qty"] = new_qty
            else:
                state["signed_qty"] = new_qty
                state["avg_entry_price"] = price
            return total_realized, total_fees

    def _build_position_states_from_snapshot(self, rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
        states: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in rows:
            symbol = str(row["symbol"])
            strategy_id = str(row.get("strategy_id") or "paper_runtime")
            alpha_family = str(row.get("alpha_family") or "runtime")
            states[_position_state_key(symbol, strategy_id, alpha_family)] = {
                "symbol": symbol,
                "strategy_id": strategy_id,
                "alpha_family": alpha_family,
                "signed_qty": float(row.get("signed_qty", 0.0) or 0.0),
                "avg_entry_price": float(row.get("avg_entry_price", 0.0) or 0.0) if row.get("avg_entry_price") is not None else None,
                "realized_pnl": float(row.get("realized_pnl", 0.0) or 0.0),
            }
        return states

    def rebuild_positions(self, as_of: str) -> list[dict[str, Any]]:
        started_at = time.perf_counter()
        store = CONTAINER.runtime_store
        watermark_created_at, watermark_fill_id = self._get_fill_watermark("positions_last_fill")
        active_rows = self._fetch_active_position_rows()
        full_rebuild_reason = None
        if not active_rows:
            full_rebuild_reason = "missing_active_snapshot"
        elif not watermark_created_at or not watermark_fill_id:
            full_rebuild_reason = "missing_fill_watermark"
        full_rebuild = full_rebuild_reason is not None
        fills_fetch_started_at = time.perf_counter()
        fills = self._fetch_new_fills(watermark_created_at, watermark_fill_id) if not full_rebuild else store.fetchall_dict(
            """
            SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
            FROM execution_fills
            ORDER BY created_at ASC, fill_id ASC
            """
        )
        fills_fetch_duration_ms = round((time.perf_counter() - fills_fetch_started_at) * 1000.0, 2)
        price_fetch_started_at = time.perf_counter()
        price_rows = store.fetchall_dict(
            "SELECT symbol, mark_price, source, price_time, quote_age_sec, stale, fallback_reason FROM market_prices_latest"
        )
        price_fetch_duration_ms = round((time.perf_counter() - price_fetch_started_at) * 1000.0, 2)
        price_by_symbol = {str(r["symbol"]): r for r in price_rows}
        state_build_started_at = time.perf_counter()
        if full_rebuild:
            states, _, _ = self._build_position_states_from_fills(fills)
        else:
            states = self._build_position_states_from_snapshot(active_rows)
            for fill in fills:
                self._apply_fill_to_position_states(states, fill)
        state_build_duration_ms = round((time.perf_counter() - state_build_started_at) * 1000.0, 2)
        affected_keys = {
            _position_state_key(
                str(fill.get("symbol") or ""),
                str(fill.get("strategy_id") or "paper_runtime"),
                str(fill.get("alpha_family") or "runtime"),
            )
            for fill in fills
        }
        if not full_rebuild and not fills:
            valued = []
            for row in active_rows:
                symbol = str(row["symbol"])
                price_meta = price_by_symbol.get(symbol) or {}
                avg_entry = float(row.get("avg_entry_price", 0.0) or 0.0)
                signed_qty = float(row.get("signed_qty", 0.0) or 0.0)
                mark = float(price_meta.get("mark_price") or row.get("mark_price") or avg_entry)
                market_value = round(signed_qty * mark, 8)
                unrealized = round((mark - avg_entry) * signed_qty, 8)
                valued.append(
                    {
                        **row,
                        "mark_price": round(mark, 8),
                        "market_value": market_value,
                        "unrealized_pnl": unrealized,
                        "exposure_notional": round(abs(market_value), 8),
                        "price_source": price_meta.get("source", row.get("price_source", "missing_mark_price")),
                        "quote_time": price_meta.get("price_time", row.get("quote_time", as_of)),
                        "quote_age_sec": float(price_meta.get("quote_age_sec", row.get("quote_age_sec", 0.0)) or 0.0),
                        "stale": bool(price_meta.get("stale", row.get("stale", False))),
                        "updated_at": as_of,
                    }
                )
            build_duration_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
            active_version = self._active_position_snapshot_version()
            self.last_rebuild_positions_metrics = {
                "snapshot_version": active_version,
                "fills_scanned": 0,
                "new_fills_applied": 0,
                "position_rows": len(valued),
                "build_duration_ms": build_duration_ms,
                "rebuild_mode": "incremental",
                "full_rebuild_reason": None,
                "fills_fetch_duration_ms": fills_fetch_duration_ms,
                "price_fetch_duration_ms": price_fetch_duration_ms,
                "state_build_duration_ms": state_build_duration_ms,
                "version_insert_duration_ms": 0.0,
                "row_materialize_duration_ms": 0.0,
                "row_write_duration_ms": 0.0,
                "activation_duration_ms": 0.0,
                "cleanup_duration_ms": 0.0,
                "history_rows_written": 0,
            }
            return valued
        active_version = self._active_position_snapshot_version()
        incremental_inplace = not full_rebuild and bool(fills) and bool(active_version)
        snapshot_version = str(active_version) if incremental_inplace else new_cycle_id()
        version_insert_duration_ms = 0.0
        row_materialize_started_at = time.perf_counter()
        latest_rows = []
        affected_latest_rows = []
        history_rows = []
        valued = []
        for state_key, state in states.items():
            symbol = str(state["symbol"])
            signed_qty = float(state["signed_qty"])
            abs_qty = abs(signed_qty)
            if abs_qty < 1e-12:
                continue
            avg_entry = float(state["avg_entry_price"] or 0.0)
            price_meta = price_by_symbol.get(symbol) or {}
            mark = float(price_meta.get("mark_price") or avg_entry)
            market_value = round(signed_qty * mark, 8)
            unrealized = round((mark - avg_entry) * signed_qty, 8)
            side = "long" if signed_qty > 0 else "short"
            row = {
                "snapshot_version": snapshot_version,
                "symbol": symbol,
                "strategy_id": state.get("strategy_id") or "paper_runtime",
                "alpha_family": state.get("alpha_family") or "runtime",
                "signed_qty": round(signed_qty, 8),
                "abs_qty": round(abs_qty, 8),
                "side": side,
                "avg_entry_price": round(avg_entry, 8),
                "mark_price": round(mark, 8),
                "market_value": market_value,
                "unrealized_pnl": unrealized,
                "realized_pnl": round(float(state.get("realized_pnl") or 0.0), 8),
                "exposure_notional": round(abs(market_value), 8),
                "price_source": price_meta.get("source", "missing_mark_price"),
                "quote_time": price_meta.get("price_time", as_of),
                "quote_age_sec": float(price_meta.get("quote_age_sec", 0.0) or 0.0),
                "stale": bool(price_meta.get("stale", False)),
                "updated_at": as_of,
            }
            latest_rows.append(row)
            if state_key in affected_keys:
                affected_latest_rows.append(row)
            if full_rebuild or state_key in affected_keys:
                history_rows.append({"snapshot_time": as_of, **{k: v for k, v in row.items() if k != "updated_at"}})
            valued.append(row)
        row_materialize_duration_ms = round((time.perf_counter() - row_materialize_started_at) * 1000.0, 2)
        row_write_duration_ms = 0.0
        build_duration_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
        activation_duration_ms = 0.0
        cleanup_duration_ms = 0.0
        transaction_started_at = time.perf_counter()
        with store._session() as conn:
            if not incremental_inplace:
                version_insert_started_at = time.perf_counter()
                store.append(
                    "position_snapshot_versions",
                    {
                        "version_id": snapshot_version,
                        "build_status": "building",
                        "snapshot_time": as_of,
                        "row_count": 0,
                        "fills_scanned": len(fills),
                        "build_duration_ms": 0.0,
                        "created_at": as_of,
                        "activated_at": None,
                    },
                    conn=conn,
                )
                version_insert_duration_ms = round((time.perf_counter() - version_insert_started_at) * 1000.0, 2)
            row_write_started_at = time.perf_counter()
            if incremental_inplace:
                for key in affected_keys:
                    store.execute(
                        """
                        DELETE FROM position_snapshots_latest
                        WHERE snapshot_version = ? AND symbol = ? AND strategy_id = ? AND alpha_family = ?
                        """,
                        [snapshot_version, key[0], key[1], key[2]],
                        conn=conn,
                    )
                if affected_latest_rows:
                    store.append("position_snapshots_latest", affected_latest_rows, conn=conn)
                if history_rows:
                    store.append("position_snapshots_history", history_rows, conn=conn)
            elif latest_rows:
                store.append("position_snapshots_latest", latest_rows, conn=conn)
                if history_rows:
                    store.append("position_snapshots_history", history_rows, conn=conn)
            row_write_duration_ms = round((time.perf_counter() - row_write_started_at) * 1000.0, 2)
            activation_started_at = time.perf_counter()
            if incremental_inplace:
                store.execute(
                    """
                    UPDATE position_snapshot_versions
                    SET snapshot_time = ?,
                        row_count = ?,
                        fills_scanned = ?,
                        build_duration_ms = ?,
                        activated_at = ?
                    WHERE version_id = ?
                    """,
                    [as_of, len(latest_rows), len(fills), build_duration_ms, as_of, snapshot_version],
                    conn=conn,
                )
            else:
                store.execute(
                    """
                    UPDATE position_snapshot_versions
                    SET build_status = 'superseded'
                    WHERE build_status = 'active'
                    """,
                    conn=conn,
                )
                store.execute(
                    """
                    UPDATE position_snapshot_versions
                    SET build_status = 'active',
                        row_count = ?,
                        fills_scanned = ?,
                        build_duration_ms = ?,
                        activated_at = ?
                    WHERE version_id = ?
                    """,
                    [len(latest_rows), len(fills), build_duration_ms, as_of, snapshot_version],
                    conn=conn,
                )
            self._set_fill_watermark("positions_last_fill", fills[-1] if fills else None, as_of, conn=conn)
            if not incremental_inplace:
                cleanup_started_at = time.perf_counter()
                store.execute(
                    """
                    DELETE FROM position_snapshots_latest
                    WHERE (snapshot_version IS NULL OR snapshot_version <> ?)
                    """,
                    [snapshot_version],
                    conn=conn,
                )
                cleanup_duration_ms = round((time.perf_counter() - cleanup_started_at) * 1000.0, 2)
            try:
                conn.commit()
            except Exception:
                pass
            activation_duration_ms = round((time.perf_counter() - activation_started_at) * 1000.0, 2)
        self.last_rebuild_positions_metrics = {
            "snapshot_version": snapshot_version,
            "fills_scanned": len(fills),
            "new_fills_applied": len(fills),
            "position_rows": len(latest_rows),
            "build_duration_ms": build_duration_ms,
            "rebuild_mode": "full" if full_rebuild else "incremental",
            "full_rebuild_reason": full_rebuild_reason,
            "fills_fetch_duration_ms": fills_fetch_duration_ms,
            "price_fetch_duration_ms": price_fetch_duration_ms,
            "state_build_duration_ms": state_build_duration_ms,
            "version_insert_duration_ms": version_insert_duration_ms,
            "row_materialize_duration_ms": row_materialize_duration_ms,
            "row_write_duration_ms": row_write_duration_ms,
            "activation_duration_ms": activation_duration_ms,
            "cleanup_duration_ms": cleanup_duration_ms,
            "history_rows_written": len(history_rows),
        }
        return valued

    def compute_equity_snapshot(self, positions: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
        started_at = time.perf_counter()
        store = CONTAINER.runtime_store
        watermark_created_at, watermark_fill_id = self._get_fill_watermark("equity_last_fill")
        previous = self._get_equity_state()
        if previous is None:
            previous = store.fetchone_dict(
                """
                SELECT cash_balance, fees_paid, realized_pnl, peak_equity
                FROM equity_snapshots
                ORDER BY snapshot_time DESC
                LIMIT 1
                """
            )
        full_rebuild_reason = None
        if previous is None:
            full_rebuild_reason = "missing_previous_snapshot"
        elif not watermark_created_at or not watermark_fill_id:
            full_rebuild_reason = "missing_fill_watermark"
        full_rebuild = full_rebuild_reason is not None
        fills = self._fetch_new_fills(watermark_created_at, watermark_fill_id) if not full_rebuild else store.fetchall_dict(
            """
            SELECT fill_id, run_id, plan_id, strategy_id, alpha_family, symbol, side, fill_qty, fill_price, fee_bps, created_at
            FROM execution_fills
            ORDER BY created_at ASC, fill_id ASC
            """
        )
        if full_rebuild:
            _, realized_total, _ = self._build_position_states_from_fills(fills)
            cash_balance, fees_paid = self._compute_cash_balance_from_fills(fills)
        else:
            prev_cash = float((previous or {}).get("cash_balance", self.initial_capital) or self.initial_capital)
            prev_fees = float((previous or {}).get("fees_paid", 0.0) or 0.0)
            prev_realized = float((previous or {}).get("realized_pnl", 0.0) or 0.0)
            if fills:
                delta_cash_balance, delta_fees = self._compute_cash_balance_from_fills(fills)
                delta_cash = round(delta_cash_balance - self.initial_capital, 8)
                delta_realized = 0.0
                delta_states: dict[str, dict[str, Any]] = {}
                for fill in fills:
                    realized_delta, _ = self._apply_fill_to_position_states(delta_states, fill)
                    delta_realized += realized_delta
                cash_balance = round(prev_cash + delta_cash, 8)
                fees_paid = round(prev_fees + delta_fees, 8)
                realized_total = round(prev_realized + delta_realized, 8)
            else:
                cash_balance = round(prev_cash, 8)
                fees_paid = round(prev_fees, 8)
                realized_total = round(prev_realized, 8)
        unrealized = round(sum(float(p.get("unrealized_pnl", 0.0) or 0.0) for p in positions), 8)
        used_margin = round(sum(float(p.get("avg_entry_price", 0.0) or 0.0) * float(p.get("abs_qty", 0.0) or 0.0) for p in positions), 8)
        current_long_notional = round(sum(max(0.0, float(p.get("market_value", 0.0) or 0.0)) for p in positions), 8)
        current_short_notional = round(sum(abs(min(0.0, float(p.get("market_value", 0.0) or 0.0))) for p in positions), 8)
        market_value = round(sum(float(p.get("market_value", 0.0) or 0.0) for p in positions), 8)
        collateral_equity = round(cash_balance + market_value, 8)
        total_equity = round(collateral_equity, 8)
        available_margin = round(max(total_equity - used_margin, 0.0), 8)
        margin_utilization = round((used_margin / max(total_equity, 1e-9)) if total_equity > 0 else 0.0, 8)
        equity_denom = max(abs(total_equity), 1e-9)
        gross = round((current_long_notional + current_short_notional) / equity_denom, 8) if positions else 0.0
        net = round(market_value / equity_denom, 8) if positions else 0.0
        prev_peak = float((previous or {}).get("peak_equity", self.initial_capital) or self.initial_capital)
        peak = max(prev_peak, total_equity)
        drawdown = round((peak - total_equity) / peak, 8) if peak else 0.0
        row = {
            "snapshot_time": as_of,
            "cash_balance": round(cash_balance, 8),
            "free_cash": round(cash_balance, 8),
            "used_margin": round(used_margin, 8),
            "collateral_equity": round(collateral_equity, 8),
            "available_margin": round(available_margin, 8),
            "margin_utilization": round(margin_utilization, 8),
            "gross_exposure": gross,
            "net_exposure": net,
            "long_exposure": round(current_long_notional / equity_denom, 8) if positions else 0.0,
            "short_exposure": round(current_short_notional / equity_denom, 8) if positions else 0.0,
            "market_value": market_value,
            "unrealized_pnl": unrealized,
            "realized_pnl": round(realized_total, 8),
            "fees_paid": round(fees_paid, 8),
            "total_equity": total_equity,
            "drawdown": drawdown,
            "peak_equity": round(peak, 8),
        }
        with store._session() as conn:
            store.append("equity_snapshots", row, conn=conn)
            self._set_fill_watermark("equity_last_fill", fills[-1] if fills else None, as_of, conn=conn)
            self._set_equity_state(row, as_of, conn=conn)
            try:
                conn.commit()
            except Exception:
                pass
        self.last_compute_equity_snapshot_metrics = {
            "fills_scanned": len(fills),
            "new_fills_applied": len(fills),
            "position_rows": len(positions),
            "build_duration_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
            "rebuild_mode": "full" if full_rebuild else "incremental",
            "full_rebuild_reason": full_rebuild_reason,
        }
        return row

    def price_runtime_config(self) -> dict[str, Any]:
        settings = getattr(self.quote_client, 'settings', None)
        return {
            'collector_mode': 'live' if getattr(settings, 'use_live_market_data', False) else 'synthetic',
            'price_source': getattr(settings, 'price_source', 'binance_book_ticker'),
            'allow_synthetic_quote_fallback': bool(getattr(settings, 'allow_synthetic_quote_fallback', True)),
            'strict_live_quotes': bool(getattr(settings, 'strict_live_quotes', False)),
            'binance_rest_base_url': getattr(settings, 'binance_rest_base_url', 'https://api.binance.com'),
            'quote_timeout_sec': float(getattr(settings, 'quote_timeout_sec', 5.0)),
        }

    def synthesize_prices(self, decisions: list[dict[str, Any]], created_at: str, mode: str) -> list[dict[str, Any]]:
        symbols = [str(decision['symbol']) for decision in decisions]
        quotes = {quote.symbol: quote.to_dict() for quote in self.quote_client.fetch_best_bid_ask_many(symbols)}
        prices: list[dict[str, Any]] = []
        for idx, decision in enumerate(decisions):
            symbol = str(decision['symbol'])
            quote = quotes.get(symbol)
            if quote is None:
                base_price = 100.0 + idx * 5.0
                spread_bps = 2.0 if mode == 'paper' else 4.0
                bid = round(base_price * (1.0 - spread_bps / 20000.0), 8)
                ask = round(base_price * (1.0 + spread_bps / 20000.0), 8)
                mid = round((bid + ask) / 2.0, 8)
                quote = {
                    'symbol': symbol,
                    'bid': bid,
                    'ask': ask,
                    'mid': mid,
                    'last': mid,
                    'mark_price': mid,
                    'source': f'{mode}_synthetic_quote_fallback',
                    'quote_time': created_at,
                    'stale': True,
                    'fallback_reason': 'missing_quote',
                }
            quote['quote_age_sec'] = float(quote.get('quote_age_sec', self._quote_age_sec(quote.get('quote_time'), created_at)) or 0.0)
            prices.append(quote)
        return prices
