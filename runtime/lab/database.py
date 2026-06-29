"""
AI Lab — Persistência SQLite.
Armazena execuções, benchmark, avaliações e cache experimental.
Usa apenas stdlib — sem dependências externas.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_DB_FILE: Path | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT    DEFAULT (datetime('now')),
    capability      TEXT    NOT NULL,
    workflow_id     TEXT    NOT NULL,
    workflow_version TEXT,
    provider        TEXT    DEFAULT 'comfyui',
    model_name      TEXT,
    gpu_model       TEXT,
    input_hash      TEXT,
    input_params    TEXT    DEFAULT '{}',
    node_overrides  TEXT    DEFAULT '{}',
    prompt_id       TEXT,
    success         INTEGER DEFAULT 1,
    error_msg       TEXT,
    upload_ms       INTEGER DEFAULT 0,
    execution_ms    INTEGER DEFAULT 0,
    download_ms     INTEGER DEFAULT 0,
    total_ms        INTEGER DEFAULT 0,
    vram_total_mb   INTEGER,
    vram_used_mb    INTEGER,
    vram_free_mb    INTEGER,
    output_count    INTEGER DEFAULT 0,
    eval_score      INTEGER,
    eval_notes      TEXT,
    eval_pros       TEXT,
    eval_cons       TEXT,
    eval_at         TEXT
);

CREATE TABLE IF NOT EXISTS cache_entries (
    cache_key   TEXT PRIMARY KEY,
    created_at  TEXT DEFAULT (datetime('now')),
    capability  TEXT,
    result_json TEXT NOT NULL,
    hit_count   INTEGER DEFAULT 0,
    last_hit    TEXT
);

CREATE INDEX IF NOT EXISTS idx_exec_capability ON executions(capability);
CREATE INDEX IF NOT EXISTS idx_exec_created    ON executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_exec_success    ON executions(success);
"""


def init(data_dir: Path) -> None:
    global _DB_FILE
    data_dir.mkdir(parents=True, exist_ok=True)
    _DB_FILE = data_dir / "lab.db"
    with _connect() as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def _connect():
    assert _DB_FILE is not None, "database.init() não foi chamado"
    conn = sqlite3.connect(str(_DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Execuções ────────────────────────────────────────────────────────────────

def save_execution(
    capability: str,
    workflow_id: str,
    success: bool,
    total_ms: int,
    input_hash: str | None = None,
    input_params: dict | None = None,
    node_overrides: dict | None = None,
    prompt_id: str | None = None,
    error_msg: str | None = None,
    upload_ms: int = 0,
    execution_ms: int = 0,
    download_ms: int = 0,
    gpu_model: str | None = None,
    vram_total_mb: int | None = None,
    vram_used_mb: int | None = None,
    vram_free_mb: int | None = None,
    output_count: int = 0,
    model_name: str | None = None,
    workflow_version: str | None = None,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO executions
               (capability, workflow_id, workflow_version, model_name, gpu_model,
                input_hash, input_params, node_overrides, prompt_id,
                success, error_msg, upload_ms, execution_ms, download_ms, total_ms,
                vram_total_mb, vram_used_mb, vram_free_mb, output_count)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                capability, workflow_id, workflow_version, model_name, gpu_model,
                input_hash,
                json.dumps(input_params or {}),
                json.dumps(node_overrides or {}),
                prompt_id,
                1 if success else 0, error_msg,
                upload_ms, execution_ms, download_ms, total_ms,
                vram_total_mb, vram_used_mb, vram_free_mb, output_count,
            )
        )
        return cur.lastrowid  # type: ignore[return-value]


def get_execution(exec_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM executions WHERE id=?", (exec_id,)).fetchone()
        return dict(row) if row else None


def list_executions(
    capability: str | None = None,
    success: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = "SELECT * FROM executions WHERE 1=1"
    params: list[Any] = []
    if capability:
        query += " AND capability=?"
        params.append(capability)
    if success is not None:
        query += " AND success=?"
        params.append(1 if success else 0)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with _connect() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def add_evaluation(exec_id: int, score: int, notes: str, pros: str, cons: str) -> None:
    with _connect() as conn:
        conn.execute(
            """UPDATE executions
               SET eval_score=?, eval_notes=?, eval_pros=?, eval_cons=?,
                   eval_at=datetime('now')
               WHERE id=?""",
            (score or None, notes or None, pros or None, cons or None, exec_id),
        )


# ── Benchmark ─────────────────────────────────────────────────────────────────

def get_benchmark_by_capability() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT
                capability,
                COUNT(*)                                              AS total,
                SUM(success)                                          AS successes,
                ROUND(100.0 * SUM(success) / COUNT(*), 1)            AS success_rate,
                ROUND(AVG(CASE WHEN success=1 THEN execution_ms END)) AS avg_exec_ms,
                MIN(CASE WHEN success=1 THEN execution_ms END)        AS min_exec_ms,
                MAX(CASE WHEN success=1 THEN execution_ms END)        AS max_exec_ms,
                ROUND(AVG(CASE WHEN success=1 THEN total_ms END))     AS avg_total_ms,
                ROUND(AVG(CASE WHEN success=1 THEN vram_used_mb END)) AS avg_vram_mb,
                ROUND(AVG(eval_score), 1)                             AS avg_score,
                COUNT(eval_score)                                     AS eval_count,
                MAX(created_at)                                       AS last_run
            FROM executions
            GROUP BY capability
            ORDER BY total DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_benchmark_by_workflow() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT
                workflow_id,
                capability,
                COUNT(*)                                              AS total,
                ROUND(100.0 * SUM(success) / COUNT(*), 1)            AS success_rate,
                ROUND(AVG(CASE WHEN success=1 THEN execution_ms END)) AS avg_exec_ms,
                ROUND(AVG(CASE WHEN success=1 THEN vram_used_mb END)) AS avg_vram_mb,
                MAX(created_at)                                       AS last_run
            FROM executions
            GROUP BY workflow_id
            ORDER BY total DESC
        """).fetchall()
        return [dict(r) for r in rows]


# ── Cache experimental ────────────────────────────────────────────────────────

def cache_get(key: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT result_json FROM cache_entries WHERE cache_key=?", (key,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE cache_entries SET hit_count=hit_count+1, last_hit=datetime('now') WHERE cache_key=?",
                (key,),
            )
            return row["result_json"]
        return None


def cache_set(key: str, capability: str, result_json: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache_entries (cache_key, capability, result_json) VALUES (?,?,?)",
            (key, capability, result_json),
        )


def cache_list() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT cache_key, created_at, capability, hit_count, last_hit FROM cache_entries ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def cache_clear(key: str | None = None) -> int:
    with _connect() as conn:
        if key:
            conn.execute("DELETE FROM cache_entries WHERE cache_key=?", (key,))
            return 1
        cur = conn.execute("DELETE FROM cache_entries")
        return cur.rowcount
