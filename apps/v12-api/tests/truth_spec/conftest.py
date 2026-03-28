from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import pytest


# Adjust these defaults to your repo.
DEFAULT_ENGINE_CLASS = os.getenv(
    "TRUTH_ENGINE_CLASS",
    "tests.truth_layer.truth_engine_adapter.TruthEngineAdapter",
)
DEFAULT_SYMBOL = os.getenv("TRUTH_TEST_SYMBOL", "BTC")
DEFAULT_STARTING_CASH = float(os.getenv("TRUTH_TEST_STARTING_CASH", "10000"))


@dataclass(frozen=True)
class FillSpec:
    fill_id: str
    side: str
    qty: float
    price: float
    symbol: str = DEFAULT_SYMBOL
    ts: int = 0
    fee: float = 0.0


@dataclass(frozen=True)
class MarkSpec:
    symbol: str
    price: float
    ts: int


def _import_string(path: str) -> Any:
    module_name, attr_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def _maybe_call(obj: Any, candidate_names: Sequence[str], *args: Any, **kwargs: Any) -> Any:
    for name in candidate_names:
        fn = getattr(obj, name, None)
        if callable(fn):
            return fn(*args, **kwargs)
    raise AttributeError(f"None of {candidate_names!r} exist on {type(obj).__name__}")


def _coerce_mapping_fill(fill: FillSpec) -> dict[str, Any]:
    return {
        "fill_id": fill.fill_id,
        "id": fill.fill_id,
        "side": fill.side,
        "qty": fill.qty,
        "price": fill.price,
        "symbol": fill.symbol,
        "ts": fill.ts,
        "timestamp": fill.ts,
        "fee": fill.fee,
    }


def _coerce_mapping_mark(mark: MarkSpec) -> dict[str, Any]:
    return {
        "symbol": mark.symbol,
        "price": mark.price,
        "mark": mark.price,
        "ts": mark.ts,
        "timestamp": mark.ts,
    }


@pytest.fixture
def engine_class() -> type:
    return _import_string(DEFAULT_ENGINE_CLASS)


@pytest.fixture
def engine(engine_class: type) -> Any:
    try:
        return engine_class(starting_cash=DEFAULT_STARTING_CASH)
    except TypeError:
        try:
            return engine_class(initial_cash=DEFAULT_STARTING_CASH)
        except TypeError:
            return engine_class()


@pytest.fixture
def symbol() -> str:
    return DEFAULT_SYMBOL


@pytest.fixture
def fill_factory() -> Any:
    def _make(**overrides: Any) -> FillSpec:
        base = FillSpec(fill_id="f-default", side="buy", qty=1.0, price=100.0)
        data = {
            "fill_id": base.fill_id,
            "side": base.side,
            "qty": base.qty,
            "price": base.price,
            "symbol": base.symbol,
            "ts": base.ts,
            "fee": base.fee,
        }
        data.update(overrides)
        return FillSpec(**data)

    return _make


@pytest.fixture
def mark_factory(symbol: str) -> Any:
    def _make(price: float, ts: int = 1, **overrides: Any) -> MarkSpec:
        data = {"symbol": symbol, "price": price, "ts": ts}
        data.update(overrides)
        return MarkSpec(**data)

    return _make


@pytest.fixture
def apply_fill() -> Any:
    def _apply(engine: Any, fill: FillSpec) -> Any:
        payload = _coerce_mapping_fill(fill)
        return _maybe_call(engine, ("apply_fill", "ingest_fill", "on_fill"), payload)

    return _apply


@pytest.fixture
def apply_mark() -> Any:
    def _apply(engine: Any, mark: MarkSpec) -> Any:
        try:
            return _maybe_call(
                engine,
                ("apply_mark", "update_mark", "on_mark"),
                mark.symbol,
                mark.price,
                mark.ts,
            )
        except TypeError:
            payload = _coerce_mapping_mark(mark)
            return _maybe_call(engine, ("apply_mark", "update_mark", "on_mark"), payload)

    return _apply


@pytest.fixture
def get_state() -> Any:
    def _get(engine: Any) -> Any:
        return _maybe_call(engine, ("get_state", "state", "snapshot"))

    return _get


@pytest.fixture
def rebuild_from_history() -> Any:
    def _rebuild(engine: Any, fills: Iterable[FillSpec], marks: Iterable[MarkSpec]) -> Any:
        fill_payloads = [_coerce_mapping_fill(f) for f in fills]
        mark_payloads = [_coerce_mapping_mark(m) for m in marks]
        return _maybe_call(
            engine,
            ("rebuild_from_history", "rebuild", "reconstruct_state"),
            fills=fill_payloads,
            marks=mark_payloads,
        )

    return _rebuild


def state_value(state: Any, *candidates: str) -> Any:
    for name in candidates:
        if isinstance(state, dict) and name in state:
            return state[name]
        if hasattr(state, name):
            return getattr(state, name)
    raise AssertionError(f"State does not contain any of: {candidates!r}")
