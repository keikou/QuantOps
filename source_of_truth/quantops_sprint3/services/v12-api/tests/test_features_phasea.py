from ai_hedge_bot.data.collectors.synthetic_market import SyntheticMarketFactory
from ai_hedge_bot.features.feature_pipeline import FeaturePipeline


def test_phasea_features_present():
    df = SyntheticMarketFactory(seed=11).build_market_frame('BTCUSDT', '15m', 200)
    features = FeaturePipeline().build(df)
    for key in ['funding_momentum', 'oi_momentum', 'trade_flow_imbalance', 'spread_zscore', 'depth_imbalance', 'liquidation_spike', 'volume_spike', 'market_regime_score', 'momentum_24', 'return_4']:
        assert key in features
