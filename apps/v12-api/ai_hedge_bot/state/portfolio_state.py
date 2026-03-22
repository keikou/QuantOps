from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortfolioState:
    data: dict[str, Any] = field(default_factory=dict)
