from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import sys

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover
    duckdb = None
    import sqlite3


class DuckDBConnectionFactory:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path))
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path = str(db_dir / ".quantops.duckdb.lock")

    @contextmanager
    def _process_lock(self):
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o666)
        try:
            if sys.platform == "win32":
                import msvcrt

                try:
                    msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
                except OSError:
                    # Best-effort fallback for Windows test environments where
                    # the lock file may already be held or the filesystem does
                    # not fully support byte-range locks.
                    pass
                yield
                try:
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    @contextmanager
    def connect(self, read_only: bool = False):
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with self._process_lock():
            if duckdb is None:
                conn = sqlite3.connect(str(db_file))
                try:
                    yield conn
                    if not read_only:
                        conn.commit()
                finally:
                    conn.close()
                return

            if read_only and not db_file.exists():
                bootstrap = duckdb.connect(str(db_file), read_only=False)
                bootstrap.close()

            conn = duckdb.connect(str(db_file), read_only=read_only)
            try:
                yield conn
            finally:
                conn.close()
