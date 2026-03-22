from ai_hedge_bot.learning.alpha_learning import AlphaWeightStore
from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.alpha.alpha_registry import ALPHA_REGISTRY


def test_default_weight_store_has_all_alphas():
    store = AlphaWeightStore(SETTINGS.weights_path)
    weights = store.load()
    assert set(ALPHA_REGISTRY).issubset(set(weights))


def test_weight_update_changes_values():
    store = AlphaWeightStore(SETTINGS.weights_path)
    old = store.load()
    updated = store.update_from_scores({'trend_alpha': 0.5, 'cross_asset_relative_momentum_alpha': -0.2})
    assert updated['trend_alpha'] != old['trend_alpha'] or updated['cross_asset_relative_momentum_alpha'] != old['cross_asset_relative_momentum_alpha']
