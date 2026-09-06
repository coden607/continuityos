from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel


class WorkflowState(BaseModel):
    workflow_id: str
    step: str
    status: Literal["pending", "running", "completed", "failed"]
    payload: dict[str, Any] = {}


class DurableWorkflowStore:
    """Zero-cost local durable state; DBOS/Temporal adapters can replace this backend."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS workflows (workflow_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def save(self, state: WorkflowState) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO workflows(workflow_id,state) VALUES (?,?) ON CONFLICT(workflow_id) DO UPDATE SET state=excluded.state, updated_at=CURRENT_TIMESTAMP",
                (state.workflow_id, state.model_dump_json()),
            )

    def load(self, workflow_id: str) -> WorkflowState | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT state FROM workflows WHERE workflow_id=?", (workflow_id,)).fetchone()
        return WorkflowState.model_validate_json(row[0]) if row else None


class DBOSAdapter:
    """Runs workflow steps through an injected DBOS-compatible runtime while preserving local recovery state."""

    def __init__(self, runtime: Any, fallback_path: str | Path) -> None:
        self.runtime = runtime
        self.store = DurableWorkflowStore(fallback_path)

    def run(self, workflow_id: str, step: str, fn, *args: Any, **kwargs: Any) -> Any:
        self.store.save(WorkflowState(workflow_id=workflow_id, step=step, status="running"))
        try:
            if hasattr(self.runtime, "run"):
                result = self.runtime.run(workflow_id, fn, *args, **kwargs)
            else:
                result = fn(*args, **kwargs)
        except Exception as exc:
            self.store.save(WorkflowState(workflow_id=workflow_id, step=step, status="failed", payload={"error": str(exc)}))
            raise
        self.store.save(WorkflowState(workflow_id=workflow_id, step=step, status="completed"))
        return result
