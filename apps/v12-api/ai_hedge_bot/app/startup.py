# apps/v12-api/ai_hedge_bot/app/startup.py
from __future__ import annotations

import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from ai_hedge_bot.services.runtime.runtime_service import RuntimeService

# 必要なら既存プロジェクト側の import に合わせて調整してください
# 例:
# from ai_hedge_bot.db.duckdb import get_duckdb_connection
# from ai_hedge_bot.services.scheduler_defaults import seed_scheduler_defaults


_RUNTIME_TASK_ATTR = "_paper_runtime_task"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_paper_cycle_interval_sec() -> int:
    raw = os.getenv("PAPER_CYCLE_INTERVAL_SEC", "60").strip()
    try:
        value = int(raw)
        return max(value, 1)
    except Exception:
        return 60


def _ensure_runtime_dir() -> None:
    runtime_dir = os.getenv("RUNTIME_DIR", "./runtime")
    Path(runtime_dir).mkdir(parents=True, exist_ok=True)


def _seed_scheduler_defaults_safe() -> None:
    """
    既存の scheduler defaults seed があるならここで呼ぶ。
    無い環境でも startup 失敗にしない。
    """
    try:
        # 既存プロジェクトに合わせて import を有効化してください
        # seed_scheduler_defaults()
        pass
    except Exception as e:
        print(f"[startup] scheduler defaults seed skipped: {e}")


def _has_paper_strategy() -> bool:
    """
    paper loop 起動可否の最小判定。
    必要なら strategy registry / env / mode 判定に差し替えてください。
    """
    mode = (os.getenv("AHB_MODE") or "").strip().lower()
    if mode == "paper":
        return True

    # 環境変数で明示的に有効化されているなら true
    if _as_bool(os.getenv("ENABLE_STARTUP_PAPER_LOOP"), default=False):
        return True

    return False


def _seed_runtime_state_safe() -> bool:
    """
    既存 seed があるならここで呼ぶ。
    戻り値はログ表示用。
    """
    try:
        # 既存関数があるならここで呼ぶ
        # result = seed_runtime_state()
        # return bool(result)
        return False
    except Exception as e:
        print(f"[startup] seed failed: {e}")
        return False


def _get_conn() -> Any | None:
    """
    DuckDB 接続取得。
    プロジェクトの実装に合わせて差し替えてください。
    """
    try:
        # return get_duckdb_connection()
        return None
    except Exception as e:
        print(f"[startup] db connection unavailable: {e}")
        return None


def _load_latest_equity_state(conn: Any | None) -> dict[str, float]:
    """
    equity_snapshots から最新 equity を取得。
    available_margin は保存列ではなく used_margin から導出する。

    実 DB に used_margin がある前提:
      total_equity
      used_margin
    """
    if conn is None:
        return {
            "total_equity": 0.0,
            "used_margin": 0.0,
            "available_margin": 0.0,
        }

    row = conn.execute(
        """
        SELECT
            total_equity,
            used_margin
        FROM equity_snapshots
        ORDER BY snapshot_time DESC
        LIMIT 1
        """
    ).fetchone()

    if not row:
        return {
            "total_equity": 0.0,
            "used_margin": 0.0,
            "available_margin": 0.0,
        }

    total_equity = float(row[0] or 0.0)
    used_margin = float(row[1] or 0.0)
    available_margin = max(total_equity - used_margin, 0.0)

    return {
        "total_equity": total_equity,
        "used_margin": used_margin,
        "available_margin": available_margin,
    }


async def _run_paper_cycle_once(runtime_service: RuntimeService) -> None:
    """
    1サイクルだけ実行。
    runtime_service.run_once() が equity_state を受け取らない実装でも壊れないように、
    まずは通常呼び出しを優先し、必要なら fallback します。
    """
    conn = _get_conn()
    equity_state = _load_latest_equity_state(conn)

    try:
        if asyncio.iscoroutinefunction(runtime_service.run_once):
            try:
                await runtime_service.run_once(
                    mode="paper",
                    triggered_by="startup_loop",
                    equity_state=equity_state,
                )
            except TypeError:
                await runtime_service.run_once(
                    mode="paper",
                    triggered_by="startup_loop",
                )
        else:
            try:
                runtime_service.run_once(
                    mode="paper",
                    triggered_by="startup_loop",
                    equity_state=equity_state,
                )
            except TypeError:
                runtime_service.run_once(
                    mode="paper",
                    triggered_by="startup_loop",
                )
    finally:
        with contextlib.suppress(Exception):
            if conn is not None:
                conn.close()

    print(
        "[paper-loop] run_once ok "
        f"total_equity={equity_state['total_equity']:.4f} "
        f"used_margin={equity_state['used_margin']:.4f} "
        f"available_margin={equity_state['available_margin']:.4f}"
    )


async def _paper_runtime_loop() -> None:
    interval_sec = _get_paper_cycle_interval_sec()
    runtime_service = RuntimeService()

    while True:
        print("[paper-loop] run_once start")
        try:
            await _run_paper_cycle_once(runtime_service)
        except Exception as e:
            print(f"[paper-loop] run_once error: {e}")

        await asyncio.sleep(interval_sec)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_runtime_dir()
    _seed_scheduler_defaults_safe()

    enable_startup_paper_loop = _as_bool(
        os.getenv("ENABLE_STARTUP_PAPER_LOOP"),
        default=False,
    )
    has_paper_strategy = _has_paper_strategy()
    seed_result = _seed_runtime_state_safe()

    print(f"[startup] ENABLE_STARTUP_PAPER_LOOP = {enable_startup_paper_loop}")
    print(f"[startup] has_paper_strategy = {has_paper_strategy}")
    print(f"[startup] seed result = {seed_result}")

    paper_task: asyncio.Task | None = None

    if enable_startup_paper_loop and has_paper_strategy:
        paper_task = asyncio.create_task(_paper_runtime_loop())
        setattr(app.state, _RUNTIME_TASK_ATTR, paper_task)

    try:
        yield
    finally:
        task = getattr(app.state, _RUNTIME_TASK_ATTR, None)
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # 既存 router 登録があるならそのまま戻してください
    # 例:
    # from ai_hedge_bot.api.routes.health import router as health_router
    # from ai_hedge_bot.api.routes.runtime import router as runtime_router
    # from ai_hedge_bot.api.routes.portfolio import router as portfolio_router
    #
    # app.include_router(health_router)
    # app.include_router(runtime_router)
    # app.include_router(portfolio_router)

    return app


app = create_app()