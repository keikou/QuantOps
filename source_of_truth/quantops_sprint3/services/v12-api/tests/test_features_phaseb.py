from ai_hedge_bot.features.feature_pipeline import FeaturePipeline
from ai_hedge_bot.data.collectors.synthetic_market import SyntheticMarketFactory


def test_feature_schema_has_40_features():
    assert len(FeaturePipeline.FEATURE_SCHEMA) == 40


def test_feature_pipeline_builds_all_features():
    frame = SyntheticMarketFactory(seed=1).build_market_frame('BTCUSDT')
    features = FeaturePipeline().build(frame)
    assert len(features) == 40
    assert 'btc_relative_strength' in features
    assert 'stress_regime_score' in features
