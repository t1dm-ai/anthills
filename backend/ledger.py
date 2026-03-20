"""
Agent Ledger — append-only log of every agent invocation.

Each entry is hashed and chained to the previous entry, making the log
tamper-evident. Long-term this structure maps cleanly onto a real blockchain.

Chain integrity:
  entry.hash = sha256(all fields including prev_hash)
  entry.prev_hash = hash of the immediately preceding entry (or None)
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# ─── Context var ──────────────────────────────────────────────────────────────
# Carried through the asyncio task so ClaudeWorkers can attach LLM call data
# to the correct ledger entry without explicit wiring.

current_entry: contextvars.ContextVar["LedgerEntry | None"] = (
    contextvars.ContextVar("current_entry", default=None)
)


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class LedgerEntry:
    # Identity
    id: str
    worker_id: str
    worker_name: str
    invocation_id: str

    # What triggered this invocation
    trigger_pheromone_id: str
    trigger_pheromone_type: str
    trail_id: str
    input_payload: dict

    # Timing
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None

    # Outcome
    status: str = "running"          # running | completed | error
    error: Optional[str] = None
    output_pheromone_type: Optional[str] = None
    output_payload: Optional[dict] = None

    # LLM-specific (ClaudeWorker only)
    messages: Optional[list] = None           # messages list sent to Claude
    raw_response_text: Optional[str] = None   # full text response
    thinking: Optional[list[str]] = None      # thinking blocks if extended thinking
    token_usage: Optional[dict] = None        # {input_tokens, output_tokens}
    model: Optional[str] = None

    # Blockchain chain fields
    prev_hash: Optional[str] = None   # hash of previous entry
    hash: Optional[str] = None        # sha256 of this entry's content

    def seal(self) -> None:
        """Compute and store the content hash, finalizing the entry."""
        content = {k: v for k, v in asdict(self).items() if k != "hash"}
        raw = json.dumps(content, sort_keys=True, default=str)
        self.hash = hashlib.sha256(raw.encode()).hexdigest()


# ─── Ledger ───────────────────────────────────────────────────────────────────

class Ledger:
    """In-memory append-only ledger. Each entry is chained to the previous."""

    def __init__(self):
        self._entries: list[LedgerEntry] = []
        self._by_id: dict[str, LedgerEntry] = {}

    # ── Write ──────────────────────────────────────────────────────────────

    def start(self, worker, pheromone, invocation_id: str) -> LedgerEntry:
        prev_hash = self._entries[-1].hash if self._entries else None
        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            worker_id=worker.id,
            worker_name=worker.name,
            invocation_id=invocation_id,
            trigger_pheromone_id=pheromone.id,
            trigger_pheromone_type=pheromone.type,
            trail_id=pheromone.trail_id,
            input_payload=dict(pheromone.payload),
            started_at=datetime.now(timezone.utc).isoformat(),
            prev_hash=prev_hash,
        )
        self._entries.append(entry)
        self._by_id[entry.id] = entry
        return entry

    def complete(
        self,
        entry: LedgerEntry,
        output_type: Optional[str] = None,
        output_payload: Optional[dict] = None,
    ) -> None:
        entry.completed_at = datetime.now(timezone.utc).isoformat()
        entry.duration_ms = _ms_since(entry.started_at)
        entry.status = "completed"
        entry.output_pheromone_type = output_type
        entry.output_payload = output_payload
        entry.seal()

    def fail(self, entry: LedgerEntry, error: str) -> None:
        entry.completed_at = datetime.now(timezone.utc).isoformat()
        entry.duration_ms = _ms_since(entry.started_at)
        entry.status = "error"
        entry.error = error
        entry.seal()

    # ── Read ───────────────────────────────────────────────────────────────

    def all(self) -> list[LedgerEntry]:
        return list(self._entries)

    def verify_chain(self) -> bool:
        """Walk the chain and verify every hash is consistent."""
        prev = None
        for entry in self._entries:
            if entry.status == "running":
                continue  # not sealed yet
            if entry.prev_hash != prev:
                return False
            content = {k: v for k, v in asdict(entry).items() if k != "hash"}
            raw = json.dumps(content, sort_keys=True, default=str)
            expected = hashlib.sha256(raw.encode()).hexdigest()
            if entry.hash != expected:
                return False
            prev = entry.hash
        return True

    # ── Serialization ──────────────────────────────────────────────────────

    def serialize(self, entry: LedgerEntry) -> dict:
        return asdict(entry)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ms_since(iso: str) -> int:
    start = datetime.fromisoformat(iso)
    now = datetime.now(timezone.utc)
    return int((now - start).total_seconds() * 1000)
