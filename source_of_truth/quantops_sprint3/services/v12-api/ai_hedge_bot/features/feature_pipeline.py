from __future__ import annotations

import pandas as pd

from .price_features import build_price_features
from .volatility_features import build_volatility_features
from .derivatives_features import build_derivatives_features
from .orderflow_features import build_orderflow_features
from .liquidity_features import build_liquidity_features
from .volume_features import build_volume_features
from .event_features import build_event_features
from .cross_asset_features import build_cross_asset_features
from .market_state_features import build_market_state_features


class FeaturePipeline:
    FEATURE_SCHEMA = [
        'return_1','return_4','return_24','momentum_1','momentum_4','momentum_24','trend_strength','price_distance_ma',
        'atr','realized_volatility','volatility_ratio','volatility_regime','volatility_zscore',
        'funding_rate','funding_deviation','funding_momentum','open_interest','oi_delta','oi_momentum',
        'orderbook_imbalance','depth_ratio','aggressive_buy_volume','aggressive_sell_volume','trade_flow_imbalance',
        'bid_ask_spread','spread_zscore','market_depth','depth_imbalance',
        'volume','volume_ma_ratio','volume_zscore','relative_volume',
        'liquidation_volume','liquidation_spike','volume_spike',
        'btc_relative_strength','eth_relative_strength',
        'market_regime_score','trend_regime_score','stress_regime_score',
    ]

    def build(self, df: pd.DataFrame) -> dict[str, float]:
        blocks = [
            build_price_features(df),
            build_volatility_features(df),
            build_derivatives_features(df),
            build_orderflow_features(df),
            build_liquidity_features(df),
            build_volume_features(df),
            build_event_features(df),
            build_cross_asset_features(df),
            build_market_state_features(df),
        ]
        out: dict[str, float] = {}
        for block in blocks:
            for key, series in block.items():
                out[key] = float(series.iloc[-1]) if len(series) else 0.0
        for key in self.FEATURE_SCHEMA:
            out.setdefault(key, 0.0)
        return out
