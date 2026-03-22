from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ai_hedge_bot.core.config import AppConfig
from ai_hedge_bot.core.enums import Mode
from ai_hedge_bot.data.pipeline_service import PipelineService
from ai_hedge_bot.state.snapshot_service import SnapshotService
from ai_hedge_bot.data.storage.runtime_store import RuntimeStore
from ai_hedge_bot.services.sprint5c_service import Sprint5CService
from ai_hedge_bot.services.sprint5d_service import Sprint5DService


@dataclass
class AppContainer:
    config: AppConfig = field(default_factory=AppConfig.from_settings)
    pipeline_service: PipelineService = field(init=False)
    snapshot_service: SnapshotService = field(init=False)
    latest_portfolio_diagnostics: dict = field(default_factory=dict)
    latest_orchestrator_run: dict = field(default_factory=dict)
    latest_execution_quality: dict = field(default_factory=dict)
    runtime_store: RuntimeStore = field(init=False)
    sprint5c_service: Sprint5CService = field(init=False)
    sprint5d_service: Sprint5DService = field(init=False)

    def __post_init__(self) -> None:
        self.pipeline_service = PipelineService(self.config.runtime_dir)
        self.snapshot_service = SnapshotService(self.config.runtime_dir / 'snapshots')
        self.runtime_store = RuntimeStore(self.config.data_db_path)
        self.sprint5c_service = Sprint5CService(self.config)
        self.sprint5d_service = Sprint5DService(self.config.data_db_path)

    @property
    def mode(self) -> Mode:
        return self.config.mode

    @property
    def runtime_dir(self) -> Path:
        return self.config.runtime_dir


CONTAINER = AppContainer()
