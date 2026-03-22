from ai_hedge_bot.data.collectors.synthetic_market import SyntheticMarketFactory
from ai_hedge_bot.features.feature_pipeline import FeaturePipeline


def test_feature_pipeline_builds_core_features():
    df = SyntheticMarketFactory(seed=1).build_market_frame('BTCUSDT')
    features = FeaturePipeline().build(df)
    for key in ['momentum_4', 'atr', 'funding_deviation', 'oi_delta', 'orderbook_imbalance', 'relative_volume']:
        assert key in features
