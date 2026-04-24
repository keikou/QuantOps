from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AlphaNode:
    kind: str
    value: str | float | int | None = None
    children: list["AlphaNode"] = field(default_factory=list)
    window: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "window": self.window,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AlphaNode":
        return cls(
            kind=str(payload.get("kind") or ""),
            value=payload.get("value"),
            window=payload.get("window"),
            children=[cls.from_dict(child) for child in list(payload.get("children") or [])],
        )

