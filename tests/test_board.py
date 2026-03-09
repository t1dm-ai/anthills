"""
Tests for the new PheromoneBoard (event-sourced).
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from anthills import Pheromone, PheromoneBoard


class TestPheromone:
    """Tests for the Pheromone dataclass."""
    
    def test_pheromone_creation(self):
        """Test creating a pheromone with required fields."""
        p = Pheromone(type="task.created", payload={"value": 42})
        
        assert p.type == "task.created"
        assert p.payload == {"value": 42}
        assert p.intensity == 1.0
        assert p.deposited_by == "system"
        assert p.id is not None
        assert p.deposited_at is not None
    
    def test_pheromone_with_all_fields(self):
        """Test creating a pheromone with all fields."""
        p = Pheromone(
            type="research.complete",
            payload={"findings": ["a", "b"]},
            intensity=0.8,
            deposited_by="worker_1",
            ttl_seconds=3600,
            trail_id="trail_123",
            metadata={"debug": True},
        )
        
        assert p.type == "research.complete"
        assert p.intensity == 0.8
        assert p.deposited_by == "worker_1"
        assert p.ttl_seconds == 3600
        assert p.trail_id == "trail_123"
        assert p.metadata == {"debug": True}
    
    def test_pheromone_expiry(self):
        """Test pheromone expiry logic."""
        # No TTL = never expires
        p1 = Pheromone(type="test", payload={})
        assert not p1.is_expired
        
        # With TTL but not expired yet
        p2 = Pheromone(type="test", payload={}, ttl_seconds=3600)
        assert not p2.is_expired
        
        # Manually create expired pheromone
        p3 = Pheromone(
            type="test",
            payload={},
            ttl_seconds=1,
            deposited_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        assert p3.is_expired


class TestPheromoneBoard:
    """Tests for the PheromoneBoard."""
    
    def test_deposit_and_read(self):
        """Test depositing and reading pheromones."""
        board = PheromoneBoard()
        
        p = board.deposit(Pheromone(
            type="task.created",
            payload={"value": 42},
        ))
        
        results = board.read(type="task.created")
        assert len(results) == 1
        assert results[0].payload == {"value": 42}
        assert results[0].id == p.id
    
    def test_type_filter(self):
        """Test reading with type filter."""
        board = PheromoneBoard()
        
        board.deposit(Pheromone(type="task.created", payload={"n": 1}))
        board.deposit(Pheromone(type="task.complete", payload={"n": 2}))
        board.deposit(Pheromone(type="research.done", payload={"n": 3}))
        
        tasks = board.read(type="task.created")
        assert len(tasks) == 1
        assert tasks[0].payload["n"] == 1
        
        all_pheromones = board.read()
        assert len(all_pheromones) == 3
    
    def test_intensity_filter(self):
        """Test reading with intensity filter."""
        board = PheromoneBoard()
        
        board.deposit(Pheromone(type="test", payload={"n": 1}, intensity=0.9))
        board.deposit(Pheromone(type="test", payload={"n": 2}, intensity=0.5))
        board.deposit(Pheromone(type="test", payload={"n": 3}, intensity=0.1))
        
        high = board.read(min_intensity=0.8)
        assert len(high) == 1
        
        medium = board.read(min_intensity=0.4)
        assert len(medium) == 2
        
        all_pheromones = board.read()
        assert len(all_pheromones) == 3
    
    def test_read_one(self):
        """Test reading a single pheromone by ID."""
        board = PheromoneBoard()
        
        p = board.deposit(Pheromone(type="test", payload={"value": 123}))
        
        result = board.read_one(p.id)
        assert result is not None
        assert result.payload == {"value": 123}
        
        assert board.read_one("nonexistent") is None
    
    def test_ttl_evaporation(self):
        """Test that expired pheromones are evaporated."""
        board = PheromoneBoard()
        
        # Non-expiring pheromone
        board.deposit(Pheromone(type="permanent", payload={}))
        
        # Expired pheromone
        board.deposit(Pheromone(
            type="temporary",
            payload={},
            ttl_seconds=1,
            deposited_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        ))
        
        # Before evaporate - expired still excluded from read
        assert len(board.read()) == 1
        assert len(board.read(include_expired=True)) == 2
        
        # Evaporate
        evaporated = board.evaporate()
        assert evaporated == 1
        
        # After evaporate
        assert len(board.read()) == 1
        assert len(board.read(include_expired=True)) == 1
    
    def test_subscriber_callback(self):
        """Test that subscribers are notified on deposit."""
        board = PheromoneBoard()
        received = []
        
        def callback(p: Pheromone):
            received.append(p)
        
        board.subscribe("task.created", callback)
        
        board.deposit(Pheromone(type="task.created", payload={"n": 1}))
        board.deposit(Pheromone(type="other", payload={"n": 2}))
        board.deposit(Pheromone(type="task.created", payload={"n": 3}))
        
        assert len(received) == 2
        assert received[0].payload["n"] == 1
        assert received[1].payload["n"] == 3
    
    def test_wildcard_subscriber(self):
        """Test wildcard subscriber receives all pheromones."""
        board = PheromoneBoard()
        received = []
        
        board.subscribe("*", lambda p: received.append(p))
        
        board.deposit(Pheromone(type="a", payload={}))
        board.deposit(Pheromone(type="b", payload={}))
        board.deposit(Pheromone(type="c", payload={}))
        
        assert len(received) == 3
    
    def test_wildcard_pattern_subscriber(self):
        """Test wildcard pattern subscriber (e.g., 'task.*')."""
        board = PheromoneBoard()
        received = []
        
        board.subscribe("task.*", lambda p: received.append(p))
        
        board.deposit(Pheromone(type="task.created", payload={}))
        board.deposit(Pheromone(type="task.completed", payload={}))
        board.deposit(Pheromone(type="research.done", payload={}))  # Should not match
        
        assert len(received) == 2
        assert all(p.type.startswith("task.") for p in received)
    
    @pytest.mark.asyncio
    async def test_concurrent_deposits(self):
        """Test concurrent async deposits."""
        import asyncio
        
        board = PheromoneBoard()
        
        async def deposit_many(prefix: str, count: int):
            for i in range(count):
                board.deposit(Pheromone(type=f"{prefix}.{i}", payload={"i": i}))
                await asyncio.sleep(0)  # Yield to other tasks
        
        # Run concurrent deposits
        await asyncio.gather(
            deposit_many("a", 10),
            deposit_many("b", 10),
        )
        
        # All deposits should be visible
        all_pheromones = board.read()
        assert len(all_pheromones) == 20
    
    def test_snapshot(self):
        """Test snapshot returns current board state."""
        board = PheromoneBoard()
        
        board.deposit(Pheromone(type="a", payload={"n": 1}))
        board.deposit(Pheromone(type="b", payload={"n": 2}))
        
        snapshot = board.snapshot()
        assert len(snapshot) == 2
    
    def test_events_ledger(self):
        """Test that all events are recorded in the ledger."""
        board = PheromoneBoard()
        
        board.deposit(Pheromone(type="a", payload={}))
        board.deposit(Pheromone(type="b", payload={}))
        
        events = board.events()
        assert len(events) == 2
        assert all(e.event_type == "deposit" for e in events)
    
    def test_replay(self):
        """Test replaying board state at a point in time."""
        board = PheromoneBoard()
        
        t1 = datetime.now(timezone.utc)
        board.deposit(Pheromone(type="a", payload={"n": 1}))
        
        t2 = datetime.now(timezone.utc)
        board.deposit(Pheromone(type="b", payload={"n": 2}))
        
        t3 = datetime.now(timezone.utc)
        
        # Replay at t1 - should be empty
        # (deposit happens after t1)
        state_before = board.replay(t1 - timedelta(seconds=1))
        assert len(state_before) == 0
        
        # Current state has both
        current = board.read()
        assert len(current) == 2
    
    def test_clear(self):
        """Test clearing the board."""
        board = PheromoneBoard()
        
        board.deposit(Pheromone(type="test", payload={}))
        assert len(board.read()) == 1
        
        board.clear()
        assert len(board.read()) == 0
        assert len(board.events()) == 0
    
    def test_wildcard_read_pattern(self):
        """Test reading with wildcard type pattern."""
        board = PheromoneBoard()
        
        board.deposit(Pheromone(type="task.created", payload={"n": 1}))
        board.deposit(Pheromone(type="task.completed", payload={"n": 2}))
        board.deposit(Pheromone(type="research.done", payload={"n": 3}))
        
        # Wildcard pattern
        tasks = board.read(type="task.*")
        assert len(tasks) == 2
        assert all(p.type.startswith("task.") for p in tasks)
        
        # Global wildcard
        all_pheromones = board.read(type="*")
        assert len(all_pheromones) == 3
        
        # Exact match still works
        exact = board.read(type="research.done")
        assert len(exact) == 1
    
    def test_type_matches_helper(self):
        """Test the _type_matches static method."""
        # Exact match
        assert PheromoneBoard._type_matches("task.created", "task.created") is True
        assert PheromoneBoard._type_matches("task.created", "task.completed") is False
        
        # Wildcard suffix
        assert PheromoneBoard._type_matches("task.created", "task.*") is True
        assert PheromoneBoard._type_matches("task.completed", "task.*") is True
        assert PheromoneBoard._type_matches("research.done", "task.*") is False
        
        # Global wildcard
        assert PheromoneBoard._type_matches("anything", "*") is True


# Run with: pytest tests/test_board.py -v
