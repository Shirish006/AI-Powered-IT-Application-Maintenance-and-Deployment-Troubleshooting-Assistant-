"""Database manager for persisting and querying troubleshooting sessions."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from database.schema import (
    CREATE_INDEXES,
    CREATE_SCHEMA_VERSION_TABLE,
    CREATE_TROUBLESHOOTING_HISTORY_TABLE,
    CURRENT_SCHEMA_VERSION,
)

logger = logging.getLogger(__name__)

ALLOWED_ORDER_BY = {
    "id": "id",
    "timestamp": "timestamp",
    "programming_language": "programming_language",
    "problem_type": "problem_type",
    "resolution_status": "resolution_status",
    "error_category": "error_category",
}


class DBManager:
    """Thread-safe SQLite database manager for troubleshooting history."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            from config.settings import settings

            self.db_path = Path(settings.db_path)
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a thread-safe connection with row factory and foreign keys."""
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create tables and indexes idempotently, and handle schema migrations."""
        with self.get_connection() as conn:
            conn.execute(CREATE_SCHEMA_VERSION_TABLE)
            cursor = conn.execute("SELECT version FROM schema_version LIMIT 1;")
            row = cursor.fetchone()

            if row is None:
                conn.execute(CREATE_TROUBLESHOOTING_HISTORY_TABLE)
                for index_sql in CREATE_INDEXES:
                    conn.execute(index_sql)
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?);",
                    (CURRENT_SCHEMA_VERSION,),
                )
            else:
                # Existing database: ensure tables and indexes exist
                conn.execute(CREATE_TROUBLESHOOTING_HISTORY_TABLE)
                for index_sql in CREATE_INDEXES:
                    conn.execute(index_sql)

    @staticmethod
    def _jsonify(val: Any) -> str:
        """Helper to serialize Python lists/dicts to JSON strings."""
        if isinstance(val, (list, dict)):
            return json.dumps(val, ensure_ascii=False)
        if isinstance(val, str):
            return val
        return json.dumps(val or [])

    @staticmethod
    def _unjsonify(val: str) -> Any:
        """Helper to deserialize JSON strings into Python objects."""
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return [val]

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert a sqlite3.Row to a dictionary with parsed JSON fields."""
        d = dict(row)
        for field in ("confirmed_facts", "possible_causes", "troubleshooting_steps", "verification_steps"):
            if field in d:
                d[field] = self._unjsonify(d[field])
        return d

    def insert_session(self, data: dict[str, Any]) -> int:
        """Insert a newly analyzed troubleshooting session. Returns the new record ID."""
        now_iso = datetime.now().astimezone().isoformat()
        timestamp = data.get("timestamp") or now_iso

        status = data.get("resolution_status", "Unresolved")
        if status not in ("Unresolved", "In Progress", "Solved"):
            status = "Unresolved"

        is_demo = 1 if data.get("is_demo") else 0

        sql = """
        INSERT INTO troubleshooting_history (
            timestamp,
            programming_language,
            problem_type,
            environment,
            application_framework,
            original_error_log,
            error_category,
            severity,
            error_summary,
            error_explanation,
            confirmed_facts,
            possible_causes,
            troubleshooting_steps,
            suggested_solution,
            verification_steps,
            resolution_status,
            is_demo,
            ai_provider,
            ai_model,
            detected_problem_type,
            resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        params = (
            timestamp,
            data.get("programming_language", "Python"),
            data.get("problem_type", "Maintenance"),
            data.get("environment", "Development"),
            data.get("application_framework", ""),
            data.get("original_error_log", ""),
            data.get("error_category", "Runtime Error"),
            data.get("severity", "Medium"),
            data.get("error_summary", "Unspecified Error"),
            data.get("error_explanation", ""),
            self._jsonify(data.get("confirmed_facts", [])),
            self._jsonify(data.get("possible_causes", [])),
            self._jsonify(data.get("troubleshooting_steps", [])),
            data.get("suggested_solution", ""),
            self._jsonify(data.get("verification_steps", [])),
            status,
            is_demo,
            data.get("ai_provider", ""),
            data.get("ai_model", ""),
            data.get("detected_problem_type", ""),
            data.get("resolved_at", ""),
        )

        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid or 0

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        """Retrieve a full session by record ID, with JSON fields deserialized."""
        sql = "SELECT * FROM troubleshooting_history WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.execute(sql, (session_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def list_sessions(
        self,
        search: str | None = None,
        language: str | None = None,
        problem_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "timestamp",
        ascending: bool = False,
    ) -> list[dict[str, Any]]:
        """List sessions with optional search and multiple filters, parameterized."""
        where_clauses: list[str] = []
        params: list[Any] = []

        if search and search.strip():
            term = f"%{search.strip()}%"
            where_clauses.append(
                """(
                    error_summary LIKE ? OR
                    original_error_log LIKE ? OR
                    error_category LIKE ? OR
                    application_framework LIKE ? OR
                    error_explanation LIKE ?
                )"""
            )
            params.extend([term, term, term, term, term])

        if language and language != "All":
            where_clauses.append("programming_language = ?")
            params.append(language)

        if problem_type and problem_type != "All":
            where_clauses.append("problem_type = ?")
            params.append(problem_type)

        if status and status != "All":
            where_clauses.append("resolution_status = ?")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        col = ALLOWED_ORDER_BY.get(order_by, "timestamp")
        direction = "ASC" if ascending else "DESC"

        sql = f"""
        SELECT * FROM troubleshooting_history
        {where_sql}
        ORDER BY {col} {direction}
        LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_dict(r) for r in cursor.fetchall()]

    def recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the N most recent sessions for the dashboard."""
        return self.list_sessions(limit=limit, offset=0, order_by="timestamp", ascending=False)

    def update_status(self, session_id: int, status: str) -> bool:
        """Update resolution status ('Unresolved', 'In Progress', 'Solved') and timestamp if solved."""
        if status not in ("Unresolved", "In Progress", "Solved"):
            raise ValueError(f"Invalid status: {status}")

        resolved_at = ""
        if status == "Solved":
            resolved_at = datetime.now().astimezone().isoformat()

        sql = """
        UPDATE troubleshooting_history
        SET resolution_status = ?,
            resolved_at = CASE WHEN ? = 'Solved' THEN ? ELSE resolved_at END
        WHERE id = ?;
        """
        with self.get_connection() as conn:
            cursor = conn.execute(sql, (status, status, resolved_at, session_id))
            return cursor.rowcount > 0

    def delete_session(self, session_id: int) -> bool:
        """Delete a record by ID."""
        sql = "DELETE FROM troubleshooting_history WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.execute(sql, (session_id,))
            return cursor.rowcount > 0

    def counts_by_status(self) -> dict[str, int]:
        """Return summary metrics for the dashboard."""
        sql = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN resolution_status = 'Unresolved' THEN 1 ELSE 0 END) AS unresolved,
            SUM(CASE WHEN resolution_status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN resolution_status = 'Solved' THEN 1 ELSE 0 END) AS solved
        FROM troubleshooting_history;
        """
        with self.get_connection() as conn:
            cursor = conn.execute(sql)
            row = cursor.fetchone()
            if row is None:
                return {"total": 0, "unresolved": 0, "in_progress": 0, "solved": 0}
            return {
                "total": row["total"] or 0,
                "unresolved": row["unresolved"] or 0,
                "in_progress": row["in_progress"] or 0,
                "solved": row["solved"] or 0,
            }
