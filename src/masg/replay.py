"""Optional local SQLite replay store with atomic request-ID consumption.

This is a local persistence primitive, not authenticated identity, distributed consensus,
or protection against an attacker who can roll back or replace the database.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


class ReplayStoreError(RuntimeError):
    """Replay storage failed; callers must fail closed."""


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


class ReplayStore:
    """Atomically consume each request_id once in this database."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def consume(self, request: dict[str, Any]) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(_canonical(request)).hexdigest()
            connection = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
            try:
                connection.execute("PRAGMA busy_timeout = 10000")
                connection.execute("PRAGMA synchronous = FULL")
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS consumed_requests (
                        request_id TEXT PRIMARY KEY,
                        request_digest TEXT NOT NULL,
                        consumed_at TEXT NOT NULL
                    )"""
                )
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        "INSERT INTO consumed_requests(request_id, request_digest, consumed_at) "
                        "VALUES (?, ?, ?)",
                        (
                            request["request_id"], digest,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                except sqlite3.IntegrityError:
                    connection.execute("ROLLBACK")
                    return False
                connection.execute("COMMIT")
                return True
            finally:
                connection.close()
        except (OSError, sqlite3.Error, KeyError, TypeError, ValueError) as exc:
            raise ReplayStoreError("replay database unavailable") from exc
