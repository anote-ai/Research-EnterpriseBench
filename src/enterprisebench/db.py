"""DuckDB persistence layer for EnterpriseBench experiments.

Tables
------
benchmark_tasks   — reusable task definitions (upserted by task_id)
experiment_runs   — one row per benchmark run
task_results      — one row per (run, task)
dimension_scores  — one row per (run, task, dimension)
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from .core import BenchmarkTask, TaskResult
from .evaluate import DimensionScore

_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "enterprisebench.duckdb"

_DDL = """
CREATE TABLE IF NOT EXISTS benchmark_tasks (
    task_id       VARCHAR PRIMARY KEY,
    vertical      VARCHAR NOT NULL,
    instruction   TEXT    NOT NULL,
    tool_schema   JSON    NOT NULL,
    expected_call JSON    NOT NULL,
    expected_output TEXT  NOT NULL,
    difficulty    VARCHAR NOT NULL,
    turns         JSON    NOT NULL,
    is_multi_turn BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_runs (
    run_id      VARCHAR   PRIMARY KEY,
    agent_name  VARCHAR   NOT NULL,
    seed        INTEGER,
    n_tasks     INTEGER   NOT NULL,
    created_at  TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS task_results (
    run_id          VARCHAR   NOT NULL,
    task_id         VARCHAR   NOT NULL,
    vertical        VARCHAR   NOT NULL,
    agent_name      VARCHAR   NOT NULL,
    predicted_call  JSON      NOT NULL,
    predicted_output TEXT     NOT NULL,
    latency_ms      DOUBLE    NOT NULL,
    cost_usd        DOUBLE    NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    PRIMARY KEY (run_id, task_id)
);

CREATE TABLE IF NOT EXISTS dimension_scores (
    run_id    VARCHAR NOT NULL,
    task_id   VARCHAR NOT NULL,
    dimension VARCHAR NOT NULL,
    score     DOUBLE  NOT NULL,
    details   JSON    NOT NULL,
    PRIMARY KEY (run_id, task_id, dimension)
);
"""


def init_db(path: str | Path = _DEFAULT_DB) -> duckdb.DuckDBPyConnection:
    """Open (or create) the DuckDB database and ensure all tables exist."""
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    conn.executescript(_DDL)
    return conn


def save_tasks(conn: duckdb.DuckDBPyConnection, tasks: list[BenchmarkTask]) -> None:
    """Upsert a list of BenchmarkTask objects into benchmark_tasks."""
    rows = [
        (
            t.task_id,
            t.vertical,
            t.instruction,
            json.dumps(t.tool_schema),
            json.dumps(t.expected_call),
            t.expected_output,
            t.difficulty,
            json.dumps(t.turns),
            t.is_multi_turn,
        )
        for t in tasks
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO benchmark_tasks
            (task_id, vertical, instruction, tool_schema, expected_call,
             expected_output, difficulty, turns, is_multi_turn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def save_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    agent_name: str,
    n_tasks: int,
    seed: int | None = None,
) -> None:
    """Record metadata for a benchmark run."""
    conn.execute(
        """
        INSERT INTO experiment_runs (run_id, agent_name, seed, n_tasks, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, agent_name, seed, n_tasks, datetime.now(timezone.utc)),
    )


def save_result(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    result: TaskResult,
    scores: dict[str, DimensionScore],
) -> None:
    """Persist a TaskResult and its dimension scores."""
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO task_results
            (run_id, task_id, vertical, agent_name, predicted_call,
             predicted_output, latency_ms, cost_usd, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            result.task_id,
            result.vertical,
            result.agent_name,
            json.dumps(result.predicted_call),
            result.predicted_output,
            result.latency_ms,
            result.cost_usd,
            now,
        ),
    )
    score_rows = [
        (run_id, result.task_id, dim, ds.score, json.dumps(ds.details))
        for dim, ds in scores.items()
    ]
    conn.executemany(
        """
        INSERT INTO dimension_scores (run_id, task_id, dimension, score, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        score_rows,
    )


def load_leaderboard(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Return per-agent aggregate scores across all runs and dimensions."""
    rows = conn.execute(
        """
        SELECT
            r.agent_name,
            s.dimension,
            ROUND(AVG(s.score), 4)    AS mean,
            ROUND(STDDEV(s.score), 4) AS std,
            COUNT(*)                  AS n_tasks
        FROM dimension_scores s
        JOIN experiment_runs r USING (run_id)
        GROUP BY r.agent_name, s.dimension
        ORDER BY r.agent_name, s.dimension
        """
    ).fetchall()
    cols = ["agent_name", "dimension", "mean", "std", "n_tasks"]
    return [dict(zip(cols, row)) for row in rows]


def load_run_summary(
    conn: duckdb.DuckDBPyConnection, run_id: str
) -> list[dict[str, Any]]:
    """Return per-dimension aggregate scores for a single run."""
    rows = conn.execute(
        """
        SELECT
            dimension,
            ROUND(AVG(score), 4)    AS mean,
            ROUND(STDDEV(score), 4) AS std,
            MIN(score)              AS min,
            MAX(score)              AS max,
            COUNT(*)                AS n
        FROM dimension_scores
        WHERE run_id = ?
        GROUP BY dimension
        ORDER BY dimension
        """,
        [run_id],
    ).fetchall()
    cols = ["dimension", "mean", "std", "min", "max", "n"]
    return [dict(zip(cols, row)) for row in rows]


def new_run_id() -> str:
    return str(uuid.uuid4())
