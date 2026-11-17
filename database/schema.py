"""Database schema definitions and migrations for SQLite."""

CURRENT_SCHEMA_VERSION = 1

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""

CREATE_TROUBLESHOOTING_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS troubleshooting_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    programming_language TEXT NOT NULL,
    problem_type TEXT NOT NULL,
    environment TEXT NOT NULL,
    application_framework TEXT DEFAULT '',
    original_error_log TEXT NOT NULL,
    error_category TEXT NOT NULL,
    severity TEXT NOT NULL,
    error_summary TEXT NOT NULL,
    error_explanation TEXT NOT NULL,
    confirmed_facts TEXT NOT NULL,
    possible_causes TEXT NOT NULL,
    troubleshooting_steps TEXT NOT NULL,
    suggested_solution TEXT NOT NULL,
    verification_steps TEXT NOT NULL,
    resolution_status TEXT NOT NULL CHECK(resolution_status IN ('Unresolved', 'In Progress', 'Solved')),
    is_demo INTEGER DEFAULT 0,
    ai_provider TEXT DEFAULT '',
    ai_model TEXT DEFAULT '',
    detected_problem_type TEXT DEFAULT '',
    resolved_at TEXT DEFAULT ''
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON troubleshooting_history(timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_history_language ON troubleshooting_history(programming_language);",
    "CREATE INDEX IF NOT EXISTS idx_history_problem_type ON troubleshooting_history(problem_type);",
    "CREATE INDEX IF NOT EXISTS idx_history_status ON troubleshooting_history(resolution_status);",
]
