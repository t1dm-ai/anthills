"""
Tests for Colony.
"""

import pytest
import asyncio

from anthills import Colony, Worker, Pheromone, PheromoneBoard


class TestColony:
    """Tests for Colony class."""
    
    def test_colony_creation(self):
        """Test creating a colony."""
        colony = Colony(name="test")
        
        assert colony.name == "test"
        assert colony.board is not None
    
    def test_colony_deposit(self):
        """Test depositing pheromones via colony."""
        colony = Colony(name="test")
        
        p = colony.deposit(type="task.created", payload={"value": 42})
        
        assert p.type == "task.created"
        assert p.payload == {"value": 42}
        assert p.trail_id is not None
    
    def test_colony_worker_decorator(self):
        """Test the @colony.worker decorator."""
        colony = Colony(name="test")
        results = []
        
        @colony.worker(reacts_to="task.created")
        async def handler(pheromone, board):
            results.append(pheromone.payload["value"])
        
        assert len(colony._workers) == 1
        assert colony._workers[0].name == "handler"
    
    @pytest.mark.asyncio
    async def test_colony_routes_pheromone_to_worker(self):
        """Test that colony routes pheromones to matching workers."""
        colony = Colony(name="test", auto_halt=True, idle_timeout=1)
        results = []
        
        @colony.worker(reacts_to="task.created")
        async def handler(pheromone, board):
            results.append(pheromone.payload["value"])
        
        colony.deposit(type="task.created", payload={"value": 42})
        await colony.run_async()
        
        assert results == [42]
    
    @pytest.mark.asyncio
    async def test_colony_chains_workers(self):
        """Test that workers can trigger other workers."""
        colony = Colony(name="test", auto_halt=True, idle_timeout=1)
        results = []
        
        @colony.worker(reacts_to="step1")
        async def first(pheromone, board):
            results.append("first")
            board.deposit(Pheromone(
                type="step2",
                payload={},
                deposited_by="first",
            ))
        
        @colony.worker(reacts_to="step2")
        async def second(pheromone, board):
            results.append("second")
        
        colony.deposit(type="step1", payload={})
        await colony.run_async()
        
        assert "first" in results
        assert "second" in results
    
    @pytest.mark.asyncio
    async def test_colony_auto_halt(self):
        """Test that colony auto-halts when idle."""
        colony = Colony(name="test", auto_halt=True, idle_timeout=1)
        
        @colony.worker(reacts_to="task")
        async def handler(pheromone, board):
            pass
        
        colony.deposit(type="task", payload={})
        
        # Should complete within a few seconds
        await asyncio.wait_for(colony.run_async(), timeout=5)
    
    @pytest.mark.asyncio
    async def test_colony_events_ledger(self):
        """Test that colony exposes the event ledger."""
        colony = Colony(name="test", auto_halt=True, idle_timeout=1)
        
        @colony.worker(reacts_to="task")
        async def handler(pheromone, board):
            pass
        
        colony.deposit(type="task", payload={})
        await colony.run_async()
        
        events = colony.events()
        assert len(events) >= 1
        assert events[0].event_type == "deposit"
    
    def test_colony_multiple_workers_same_type(self):
        """Test multiple workers reacting to the same type."""
        colony = Colony(name="test")
        
        @colony.worker(reacts_to="task")
        async def worker1(pheromone, board):
            pass
        
        @colony.worker(reacts_to="task")
        async def worker2(pheromone, board):
            pass
        
        assert len(colony._workers) == 2


class TestColonyIntegration:
    """Integration tests for Colony."""
    
    @pytest.mark.asyncio
    async def test_minimal_working_example(self):
        """Test the minimal working example from the spec."""
        colony = Colony(name="test", auto_halt=True, idle_timeout=1)
        results = []
        
        @colony.worker(reacts_to="task.created")
        async def handler(pheromone, board):
            results.append(pheromone.payload["value"])
        
        colony.deposit(type="task.created", payload={"value": 42})
        colony.run()
        
        assert results == [42]
    
    @pytest.mark.asyncio
    async def test_multi_step_pipeline(self):
        """Test a multi-step processing pipeline."""
        colony = Colony(name="pipeline", auto_halt=True, idle_timeout=2)
        results = []
        
        @colony.worker(reacts_to="input")
        async def step1(pheromone, board):
            value = pheromone.payload["value"]
            board.deposit(Pheromone(
                type="processed",
                payload={"value": value * 2},
                deposited_by="step1",
                trail_id=pheromone.trail_id,
            ))
        
        @colony.worker(reacts_to="processed")
        async def step2(pheromone, board):
            value = pheromone.payload["value"]
            results.append(value + 1)
        
        colony.deposit(type="input", payload={"value": 10})
        await colony.run_async()
        
        # 10 * 2 + 1 = 21
        assert results == [21]


# Run with: pytest tests/test_colony.py -v
