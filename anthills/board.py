"""
Pheromone Board: Event-sourced shared environment for agent coordination.

The board is an append-only event log. All state is derived by replaying events.
Agents deposit pheromones; other agents subscribe and react.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Awaitable


@dataclass
class Pheromone:
    """
    A signal deposited by an agent on the pheromone board.
    
    Attributes:
        type: Signal type, dot-namespaced (e.g., 'task.created', 'research.complete')
        payload: Arbitrary JSON-serializable data
        intensity: Signal strength (0.0-1.0), decays over time
        deposited_by: Worker ID or 'system'
        ttl_seconds: Time-to-live; None = no expiry
        trail_id: Links pheromone to a logical trail/task chain
        metadata: Optional tags, labels, debug info
        id: Unique identifier (auto-generated)
        deposited_at: Timestamp of deposit (auto-generated)
    """
    type: str
    payload: dict
    intensity: float = 1.0
    deposited_by: str = "system"
    ttl_seconds: int | None = None
    trail_id: str | None = None
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deposited_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_expired(self) -> bool:
        """Check if this pheromone has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.deposited_at).total_seconds()
        return elapsed >= self.ttl_seconds


@dataclass
class BoardEvent:
    """An event in the board's append-only log."""
    event_type: str  # 'deposit', 'evaporated'
    pheromone_id: str
    pheromone: Pheromone | None  # None for evaporation events
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class PheromoneBoard:
    """
    Event-sourced pheromone board.
    
    All mutations are appended as events. Current state is computed
    by replaying events. This enables full audit trails and time-travel.
    """
    
    def __init__(self):
        self._events: list[BoardEvent] = []
        self._subscribers: dict[str, list[Callable[[Pheromone], Awaitable[None] | None]]] = {}
        self._lock = asyncio.Lock()
    
    def deposit(self, pheromone: Pheromone) -> Pheromone:
        """
        Deposit a pheromone onto the board.
        
        Appends a 'deposit' event and notifies subscribers.
        
        Args:
            pheromone: The pheromone to deposit
            
        Returns:
            The deposited pheromone (with generated id/timestamp if not set)
        """
        event = BoardEvent(
            event_type="deposit",
            pheromone_id=pheromone.id,
            pheromone=pheromone,
        )
        self._events.append(event)
        self._notify(pheromone)
        return pheromone
    
    def read(
        self,
        type: str | None = None,
        min_intensity: float = 0.0,
        include_expired: bool = False,
    ) -> list[Pheromone]:
        """
        Read pheromones from the board.
        
        Computes a materialized view from the event log.
        
        Args:
            type: Filter by pheromone type (None = all types)
            min_intensity: Minimum intensity threshold
            include_expired: Include TTL-expired pheromones
            
        Returns:
            List of matching pheromones
        """
        # Build current state from events
        active: dict[str, Pheromone] = {}
        evaporated: set[str] = set()
        
        for event in self._events:
            if event.event_type == "deposit" and event.pheromone:
                active[event.pheromone_id] = event.pheromone
            elif event.event_type == "evaporated":
                evaporated.add(event.pheromone_id)
        
        # Filter results
        results = []
        for pid, p in active.items():
            if pid in evaporated:
                continue
            if not include_expired and p.is_expired:
                continue
            if type is not None and not self._type_matches(p.type, type):
                continue
            if p.intensity < min_intensity:
                continue
            results.append(p)
        
        # Sort by deposited_at descending (most recent first)
        results.sort(key=lambda p: p.deposited_at, reverse=True)
        return results
    
    @staticmethod
    def _type_matches(pheromone_type: str, pattern: str) -> bool:
        """
        Check if a pheromone type matches a pattern.
        
        Supports:
        - Exact match: "task.created" matches "task.created"
        - Wildcard suffix: "task.*" matches "task.created", "task.complete"
        - Global wildcard: "*" matches everything
        """
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return pheromone_type.startswith(prefix + ".")
        return pheromone_type == pattern
    
    def read_one(self, id: str) -> Pheromone | None:
        """Read a single pheromone by ID."""
        for event in reversed(self._events):
            if event.event_type == "deposit" and event.pheromone_id == id:
                return event.pheromone
        return None
    
    def subscribe(
        self,
        type: str,
        callback: Callable[[Pheromone], Awaitable[None] | None],
    ) -> None:
        """
        Subscribe to pheromones of a specific type.
        
        Args:
            type: Pheromone type to subscribe to ('*' for all)
            callback: Function to call when matching pheromone is deposited
        """
        self._subscribers.setdefault(type, []).append(callback)
    
    def _notify(self, pheromone: Pheromone) -> None:
        """Notify subscribers of a new pheromone."""
        # Exact type match
        for cb in self._subscribers.get(pheromone.type, []):
            self._invoke_callback(cb, pheromone)
        
        # Wildcard subscribers (e.g., "task.*" matches "task.created")
        for pattern, callbacks in self._subscribers.items():
            if pattern == pheromone.type:
                continue  # Already handled above
            if pattern == "*":
                for cb in callbacks:
                    self._invoke_callback(cb, pheromone)
            elif pattern.endswith(".*"):
                prefix = pattern[:-2]  # Remove ".*"
                if pheromone.type.startswith(prefix + "."):
                    for cb in callbacks:
                        self._invoke_callback(cb, pheromone)
    
    def _invoke_callback(
        self,
        callback: Callable[[Pheromone], Awaitable[None] | None],
        pheromone: Pheromone,
    ) -> None:
        """Invoke a callback, handling both sync and async."""
        result = callback(pheromone)
        if asyncio.iscoroutine(result):
            # Schedule async callback
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(result)
            except RuntimeError:
                # No running loop, run synchronously
                asyncio.run(result)
    
    def evaporate(self) -> int:
        """
        Mark TTL-expired pheromones as evaporated.
        
        Appends 'evaporated' events — does NOT delete log entries.
        
        Returns:
            Number of pheromones evaporated
        """
        evaporated_count = 0
        already_evaporated: set[str] = set()
        
        # Find already evaporated
        for event in self._events:
            if event.event_type == "evaporated":
                already_evaporated.add(event.pheromone_id)
        
        # Find newly expired
        for event in self._events:
            if event.event_type != "deposit" or not event.pheromone:
                continue
            if event.pheromone_id in already_evaporated:
                continue
            if event.pheromone.is_expired:
                self._events.append(BoardEvent(
                    event_type="evaporated",
                    pheromone_id=event.pheromone_id,
                    pheromone=None,
                ))
                evaporated_count += 1
        
        return evaporated_count
    
    def snapshot(self) -> list[Pheromone]:
        """Return full board state (all non-evaporated, non-expired pheromones)."""
        return self.read()
    
    def events(self) -> list[BoardEvent]:
        """Return the full event log (ledger)."""
        return list(self._events)
    
    def replay(self, as_of: datetime) -> list[Pheromone]:
        """
        Reconstruct board state at a specific point in time.
        
        Args:
            as_of: Timestamp to replay to
            
        Returns:
            Board state as it was at that timestamp
        """
        active: dict[str, Pheromone] = {}
        evaporated: set[str] = set()
        
        for event in self._events:
            if event.timestamp > as_of:
                break
            if event.event_type == "deposit" and event.pheromone:
                active[event.pheromone_id] = event.pheromone
            elif event.event_type == "evaporated":
                evaporated.add(event.pheromone_id)
        
        # Filter out evaporated, but check expiry against as_of time
        results = []
        for pid, p in active.items():
            if pid in evaporated:
                continue
            # Check if expired at as_of time
            if p.ttl_seconds is not None:
                elapsed = (as_of - p.deposited_at).total_seconds()
                if elapsed >= p.ttl_seconds:
                    continue
            results.append(p)
        
        results.sort(key=lambda p: p.deposited_at, reverse=True)
        return results
    
    def clear(self) -> None:
        """Clear all events (for testing only)."""
        self._events.clear()
        self._subscribers.clear()
