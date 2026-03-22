from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os

import duckdb


class DuckDBConnectionFactory:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path))
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path = str(db_dir / ".quantops.duckdb.lock")

    @contextmanager
    def _process_lock(self):
        """Cross-process mutex for DuckDB access.

        DuckDB only supports read/write concurrency within a single process.
        Our deployment has separate API and worker containers touching the same
        database file, so we serialize all access with an OS-level file lock,
        then open the database for the duration of a single operation and close
        it immediately afterward.
        """
        import fcntl

        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o666)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    @contextmanager
    def connect(self, read_only: bool = False):
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with self._process_lock():
            # Avoid read-only open failures during cold start. We bootstrap the
            # file once, then reopen with the requested mode.
            if read_only and not db_file.exists():
                bootstrap = duckdb.connect(str(db_file), read_only=False)
                bootstrap.close()

            conn = duckdb.connect(str(db_file), read_only=read_only)
            try:
                yield conn
            finally:
                conn.close()
