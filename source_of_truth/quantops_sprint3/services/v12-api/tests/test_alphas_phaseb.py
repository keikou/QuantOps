from ai_hedge_bot.alpha.alpha_registry import ALPHA_REGISTRY
from ai_hedge_bot.alpha.basic_alphas import ALPHA_FUNCTIONS
from ai_hedge_bot.data.collectors.synthetic_market import SyntheticMarketFactory
from ai_hedge_bot.features.feature_pipeline import FeaturePipeline


def test_alpha_registry_has_20_alphas():
    assert len(ALPHA_REGISTRY) == 20


def test_alpha_functions_has_20_entries():
    assert len(ALPHA_FUNCTIONS) == 20


def test_new_phaseb_alphas_execute():
    frame = SyntheticMarketFactory(seed=2).build_market_frame('ETHUSDT')
    f = FeaturePipeline().build(frame)
    names = {fn.__name__ for fn in ALPHA_FUNCTIONS}
    expected = {'vwap_mean_reversion_alpha','volatility_band_reversion_alpha','liquidity_sweep_reversion_alpha','funding_mean_reversion_alpha','oi_momentum_trend_alpha','cross_asset_relative_momentum_alpha'}
    assert expected.issubset(names)
    results = [fn(f) for fn in ALPHA_FUNCTIONS]
    assert len(results) == 20
