"""
Database
========
SQLite-backed store for file scan history, classification results,
and duplicate tracking.
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FileRecord:
    file_path: str
    file_name: str
    extension: str
    size_bytes: int
    label: str
    confidence: float
    image_hash: Optional[str]
    destination: str
    scanned_at: str
    moved: bool


class Database:
    """Thin wrapper around SQLite for the organizer."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    # ------------------------------------------------------------------ #
    #  Schema                                                              #
    # ------------------------------------------------------------------ #

    def _migrate(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path    TEXT    NOT NULL UNIQUE,
                file_name    TEXT    NOT NULL,
                extension    TEXT    NOT NULL,
                size_bytes   INTEGER NOT NULL,
                label        TEXT    NOT NULL,
                confidence   REAL    NOT NULL,
                image_hash   TEXT,
                destination  TEXT    NOT NULL,
                scanned_at   TEXT    NOT NULL,
                moved        INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS scan_runs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at   TEXT    NOT NULL,
                finished_at  TEXT,
                files_found  INTEGER DEFAULT 0,
                files_moved  INTEGER DEFAULT 0
            );
        """)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    #  File Records                                                        #
    # ------------------------------------------------------------------ #

    def upsert_file(self, record: FileRecord) -> int:
        """Insert or replace a file record. Returns the row id."""
        cur = self._conn.execute(
            """
            INSERT INTO files
                (file_path, file_name, extension, size_bytes, label, confidence,
                 image_hash, destination, scanned_at, moved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                label       = excluded.label,
                confidence  = excluded.confidence,
                image_hash  = excluded.image_hash,
                destination = excluded.destination,
                scanned_at  = excluded.scanned_at,
                moved       = excluded.moved
            """,
            (
                record.file_path,
                record.file_name,
                record.extension,
                record.size_bytes,
                record.label,
                record.confidence,
                record.image_hash,
                record.destination,
                record.scanned_at,
                int(record.moved),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def mark_moved(self, file_path: str, destination: str):
        self._conn.execute(
            "UPDATE files SET moved = 1, destination = ? WHERE file_path = ?",
            (destination, file_path),
        )
        self._conn.commit()

    def already_processed(self, file_path: str) -> bool:
        """Return True if a file has already been moved in a previous scan."""
        row = self._conn.execute(
            "SELECT moved FROM files WHERE file_path = ?", (file_path,)
        ).fetchone()
        return bool(row and row["moved"])

    def get_image_hashes(self) -> list[str]:
        """Return all known image hashes for duplicate detection."""
        rows = self._conn.execute(
            "SELECT image_hash FROM files WHERE image_hash IS NOT NULL"
        ).fetchall()
        return [r["image_hash"] for r in rows]

    # ------------------------------------------------------------------ #
    #  Scan Runs                                                           #
    # ------------------------------------------------------------------ #

    def start_run(self) -> int:
        cur = self._conn.execute(
            "INSERT INTO scan_runs (started_at) VALUES (?)",
            (datetime.utcnow().isoformat(),),
        )
        self._conn.commit()
        return cur.lastrowid

    def finish_run(self, run_id: int, files_found: int, files_moved: int):
        self._conn.execute(
            """
            UPDATE scan_runs
            SET finished_at = ?, files_found = ?, files_moved = ?
            WHERE id = ?
            """,
            (datetime.utcnow().isoformat(), files_found, files_moved, run_id),
        )
        self._conn.commit()

    def get_stats(self) -> dict:
        """Return aggregate stats for CLI summary."""
        row = self._conn.execute(
            "SELECT COUNT(*) as total, SUM(moved) as moved FROM files"
        ).fetchone()
        runs = self._conn.execute("SELECT COUNT(*) as runs FROM scan_runs").fetchone()
        return {
            "total_files": row["total"],
            "files_moved": int(row["moved"] or 0),
            "scan_runs": runs["runs"],
        }

    # ------------------------------------------------------------------ #
    #  Maintenance                                                         #
    # ------------------------------------------------------------------ #

    def reset(self):
        """Drop all data (keeps schema)."""
        self._conn.executescript("DELETE FROM files; DELETE FROM scan_runs;")
        self._conn.commit()
        logger.info("Database cleared.")

    def close(self):
        self._conn.close()
