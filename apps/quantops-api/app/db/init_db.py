import os

from app.db.migrate import run_migrations
from app.repositories.duckdb import DuckDBConnectionFactory
from app.repositories.risk_repository import RiskRepository
from app.repositories.analytics_repository import AnalyticsRepository


def init_db() -> None:
    db_path = os.getenv("QUANTOPS_DB_PATH", "/app/data/quantops.duckdb")
    run_migrations(db_path)
    factory = DuckDBConnectionFactory(db_path)

    with factory.connect() as conn:
        RiskRepository(factory)._ensure_tables(conn)
        AnalyticsRepository(factory)._ensure_tables(conn)
