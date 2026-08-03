"""
Checkpointing and Recovery Module.

Saves a JSON-serializable snapshot of the graph state to both SQL
(`checkpoints` table) and disk (`storage/checkpoints/<run_id>/`) after
each major workflow step, and can resume a run from the last successful
checkpoint if a node fails partway through.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from database.models import Checkpoint
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("checkpointing")
checkpoint_repo = Repository(Checkpoint)


def _serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ORM objects in the state into plain dicts for JSON storage."""
    serializable: Dict[str, Any] = {}
    for key, value in state.items():
        if isinstance(value, list):
            serializable[key] = [
                item.to_dict() if hasattr(item, "to_dict") else item for item in value
            ]
        elif hasattr(value, "to_dict"):
            serializable[key] = value.to_dict()
        else:
            serializable[key] = value
    return serializable


def save_checkpoint(session: Session, run_id: str, node_name: str, state: Dict[str, Any]) -> Checkpoint:
    snapshot = _serialize_state(state)
    record = Checkpoint(
        id=new_id("ckpt"),
        run_id=run_id,
        node_name=node_name,
        state_snapshot=json.dumps(snapshot, default=str),
        created_at=iso_now(),
    )
    checkpoint_repo.insert(session, record)
    session.flush()

    # Also mirror to disk for out-of-band recovery / debugging.
    run_dir = Path(settings.checkpoint_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"{node_name}.json").write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")

    logger.info(f"Checkpoint saved: run={run_id} node={node_name}")
    return record


def load_latest_checkpoint(session: Session, run_id: str) -> Optional[Dict[str, Any]]:
    """Return the most recent checkpoint's state snapshot for a run, if any."""
    rows = checkpoint_repo.filter_by(session, run_id=run_id)
    if not rows:
        return None
    latest = max(rows, key=lambda r: r.created_at)
    logger.info(f"Resuming run={run_id} from checkpoint node={latest.node_name}")
    return json.loads(latest.state_snapshot)


def list_checkpoints(session: Session, run_id: str):
    return sorted(checkpoint_repo.filter_by(session, run_id=run_id), key=lambda r: r.created_at)


def _to_namespace(value: Any) -> Any:
    """Recursively turn plain dicts back into attribute-accessible objects
    (types.SimpleNamespace) so recovered state can be used by agents that
    expect `.attribute` access, exactly like the original ORM objects."""
    import types

    if isinstance(value, list):
        return [_to_namespace(v) for v in value]
    if isinstance(value, dict):
        return types.SimpleNamespace(**{k: _to_namespace(v) for k, v in value.items()})
    return value


def deserialize_checkpoint_state(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a JSON checkpoint snapshot back into a usable PipelineState.

    Scalar fields (run_id, flags, error) pass through unchanged; list
    fields that held ORM rows (raw_sources, entities, ...) are rebuilt
    as SimpleNamespace objects so downstream agents can keep using
    attribute access (`source.is_rejected`, `entity.canonical_name`, ...)
    exactly as they would on the original objects.
    """
    return {key: _to_namespace(value) for key, value in snapshot.items()}


def last_successful_node(session: Session, run_id: str) -> Optional[str]:
    checkpoints = list_checkpoints(session, run_id)
    return checkpoints[-1].node_name if checkpoints else None
