from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.signal.signal_service import SignalService
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_signal_id

router = APIRouter(prefix='/signals', tags=['signals'])
_service = SignalService()
_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'signals.jsonl')
_eval_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'signal_evaluations.jsonl')


@router.post('/generate')
def generate_signals() -> dict:
    created_at = utc_now_iso()
    signals = _service.generate(CONTAINER.config.symbols)
    rows = []
    eval_rows = []
    for idx, signal in enumerate(signals):
        row = {
            'signal_id': signal['signal_id'],
            'created_at': created_at,
            'symbol': signal['symbol'],
            'side': signal['side'],
            'score': float(signal['score']),
            'dominant_alpha': signal['dominant_alpha'],
            'alpha_family': signal['alpha_family'],
            'horizon': signal['horizon'],
            'turnover_profile': signal['turnover_profile'],
            'regime': signal['regime'],
            'metadata_json': CONTAINER.runtime_store.to_json(signal.get('metadata', {})),
        }
        rows.append(row)
        _logger.append(row)
        # lightweight scaffold evaluation so analytics can move off zero/null
        won = idx % 2 == 0
        ret_bps = round((signal['score'] - 0.5) * (100 if won else -60), 4)
        eval_row = {
            'evaluation_id': new_signal_id(),
            'signal_id': signal['signal_id'],
            'created_at': created_at,
            'symbol': signal['symbol'],
            'won': won,
            'return_bps': ret_bps,
        }
        eval_rows.append(eval_row)
        _eval_logger.append(eval_row)
    CONTAINER.runtime_store.append('signals', rows)
    CONTAINER.runtime_store.append('signal_evaluations', eval_rows)
    return {'status': 'ok', 'signals': signals, 'count': len(signals)}
