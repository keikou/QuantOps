from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_hedge_bot.data.collectors.synthetic_market import SyntheticMarketFactory
from ai_hedge_bot.data.contracts.market_snapshot import MarketSnapshot
from ai_hedge_bot.data.normalization.schema_normalizer import normalize_payload
from ai_hedge_bot.data.normalization.symbol_mapper import map_symbol
from ai_hedge_bot.data.normalization.timestamp_aligner import align_timestamp
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger


class PipelineService:
    def __init__(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.collector = SyntheticMarketFactory(seed=7)
        self.raw_log = JsonlLogger(self.runtime_dir / 'market_raw.jsonl')
        self.norm_log = JsonlLogger(self.runtime_dir / 'market_normalized.jsonl')
        self._last_raw_batch: list[dict[str, Any]] = []
        self._last_normalized_batch: list[dict[str, Any]] = []

    def collect(self, symbols: list[str]) -> dict[str, Any]:
        batch: list[dict[str, Any]] = []
        for symbol in symbols:
            frame = self.collector.build_market_frame(symbol=symbol, limit=1)
            row = frame.iloc[-1].to_dict()
            payload = {
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'funding': float(row.get('funding_rate', 0.0)),
                'open_interest': float(row.get('open_interest', 0.0)),
                'liquidation_value': float(row.get('liquidation_volume', 0.0)),
                'orderbook_imbalance': self._imbalance(float(row.get('bid_depth', 0.0)), float(row.get('ask_depth', 0.0))),
                'metadata': {
                    'collector': 'synthetic_market',
                    'bid_depth': float(row.get('bid_depth', 0.0)),
                    'ask_depth': float(row.get('ask_depth', 0.0)),
                },
            }
            self.raw_log.append(payload)
            batch.append(payload)
        self._last_raw_batch = batch
        return {
            'status': 'ok',
            'batch_size': len(batch),
            'symbols': [item['symbol'] for item in batch],
            'items': batch,
        }

    def normalize(self) -> dict[str, Any]:
        normalized: list[dict[str, Any]] = []
        for item in self._last_raw_batch:
            payload = normalize_payload(item)
            mapped_symbol = map_symbol(str(payload['symbol']))
            ts = align_timestamp(str(payload['timestamp']))
            snapshot = MarketSnapshot(
                symbol=mapped_symbol,
                timestamp=ts,
                close=float(payload['close']),
                volume=float(payload.get('volume', 0.0)),
                funding=float(payload.get('funding', 0.0)),
                open_interest=float(payload.get('open_interest', 0.0)),
                liquidation_value=float(payload.get('liquidation_value', 0.0)),
                orderbook_imbalance=float(payload.get('orderbook_imbalance', 0.0)),
                metadata=dict(payload.get('metadata', {})),
            )
            row = snapshot.to_dict()
            self.norm_log.append(row)
            normalized.append(row)
        self._last_normalized_batch = normalized
        return {
            'status': 'ok',
            'batch_size': len(normalized),
            'symbols': [item['symbol'] for item in normalized],
            'items': normalized,
        }

    def latest_normalized(self) -> list[dict[str, Any]]:
        return list(self._last_normalized_batch)

    @staticmethod
    def _imbalance(bid_depth: float, ask_depth: float) -> float:
        denom = bid_depth + ask_depth
        if denom <= 0:
            return 0.0
        return round((bid_depth - ask_depth) / denom, 6)
