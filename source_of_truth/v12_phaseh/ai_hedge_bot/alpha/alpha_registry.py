from __future__ import annotations

from ai_hedge_bot.core.types import AlphaMetadata


ALPHA_REGISTRY = {
    'trend_alpha': AlphaMetadata('trend_alpha', 'momentum', 'trend', 'short', 'medium', ['momentum_4', 'trend_strength']),
    'mean_reversion_alpha': AlphaMetadata('mean_reversion_alpha', 'mean_reversion', 'reversal', 'short', 'medium', ['return_1', 'volatility_zscore']),
    'breakout_alpha': AlphaMetadata('breakout_alpha', 'momentum', 'breakout', 'short', 'high', ['momentum_24', 'volume_zscore']),
    'funding_squeeze_alpha': AlphaMetadata('funding_squeeze_alpha', 'derivatives', 'carry', 'short', 'medium', ['funding_rate', 'funding_deviation']),
    'oi_divergence_alpha': AlphaMetadata('oi_divergence_alpha', 'derivatives', 'flow', 'short', 'medium', ['oi_delta', 'return_1']),
    'liquidation_hunt_alpha': AlphaMetadata('liquidation_hunt_alpha', 'event', 'reversal', 'short', 'high', ['liquidation_spike', 'spread_zscore']),
    'orderbook_imbalance_alpha': AlphaMetadata('orderbook_imbalance_alpha', 'orderflow', 'imbalance', 'short', 'high', ['orderbook_imbalance', 'trade_flow_imbalance']),
    'volume_spike_alpha': AlphaMetadata('volume_spike_alpha', 'event', 'breakout', 'short', 'high', ['volume_spike', 'relative_volume']),
    'multi_horizon_momentum_alpha': AlphaMetadata('multi_horizon_momentum_alpha', 'momentum', 'trend', 'short', 'medium', ['momentum_1', 'momentum_4', 'momentum_24']),
    'short_term_reversal_alpha': AlphaMetadata('short_term_reversal_alpha', 'mean_reversion', 'reversal', 'short', 'medium', ['return_1', 'spread_zscore']),
    'funding_carry_alpha': AlphaMetadata('funding_carry_alpha', 'derivatives', 'carry', 'short', 'medium', ['funding_rate', 'funding_momentum']),
    'aggressive_trade_flow_alpha': AlphaMetadata('aggressive_trade_flow_alpha', 'orderflow', 'flow', 'short', 'high', ['trade_flow_imbalance', 'aggressive_buy_volume', 'aggressive_sell_volume']),
    'liquidation_cascade_alpha': AlphaMetadata('liquidation_cascade_alpha', 'event', 'breakout', 'short', 'high', ['liquidation_spike', 'return_4']),
    'volatility_expansion_alpha': AlphaMetadata('volatility_expansion_alpha', 'volatility', 'breakout', 'short', 'medium', ['volatility_ratio', 'volume_spike', 'trend_strength']),
    'vwap_mean_reversion_alpha': AlphaMetadata('vwap_mean_reversion_alpha', 'mean_reversion', 'reversal', 'short', 'medium', ['price_distance_ma', 'volume']),
    'volatility_band_reversion_alpha': AlphaMetadata('volatility_band_reversion_alpha', 'mean_reversion', 'reversal', 'short', 'medium', ['price_distance_ma', 'atr']),
    'liquidity_sweep_reversion_alpha': AlphaMetadata('liquidity_sweep_reversion_alpha', 'mean_reversion', 'reversal', 'short', 'high', ['liquidation_spike', 'depth_imbalance', 'spread_zscore']),
    'funding_mean_reversion_alpha': AlphaMetadata('funding_mean_reversion_alpha', 'derivatives', 'reversal', 'short', 'medium', ['funding_deviation']),
    'oi_momentum_trend_alpha': AlphaMetadata('oi_momentum_trend_alpha', 'derivatives', 'trend', 'short', 'medium', ['oi_momentum', 'momentum_4']),
    'cross_asset_relative_momentum_alpha': AlphaMetadata('cross_asset_relative_momentum_alpha', 'statistical', 'relative_strength', 'short', 'medium', ['btc_relative_strength', 'eth_relative_strength']),
}
