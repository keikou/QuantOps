from __future__ import annotations

from pathlib import Path
import json


class SnapshotService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, payload: dict) -> str:
        path = self.root / f'{name}.json'
        with path.open('w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return str(path)

    def load(self, name: str) -> dict:
        path = self.root / f'{name}.json'
        if not path.exists():
            return {'status': 'missing', 'name': name}
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
