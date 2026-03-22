from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    BACKTEST = 'backtest'
    PAPER = 'paper'
    SHADOW = 'shadow'
    LIVE = 'live'


class Side(str, Enum):
    LONG = 'long'
    SHORT = 'short'
    FLAT = 'flat'


class Regime(str, Enum):
    TREND = 'trend'
    MEAN_REVERSION = 'mean_reversion'
    VOLATILE = 'volatile'
    NEUTRAL = 'neutral'
