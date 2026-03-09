"""
Tests for Worker and WorkerContext.
"""

import pytest
import asyncio

from anthills import Worker, WorkerContext, Pheromone, PheromoneBoard, Colony


class TestWorkerContext:
    """Tests for WorkerContext."""
    
    def test_context_deposit_inherits_trail(self):
        """Test that deposit() inherits trail_id."""
        board = PheromoneBoard()
        colony = Colony(name="test", board=board)
        
        triggering = Pheromone(
            type="trigger",
            payload={},
            trail_id="trail_123",
        )
        
        ctx = WorkerContext(
            pheromone=triggering,
            board=board,
            colony=colony,
            worker_id="worker_1",
        )
        
        new_p = ctx.deposit(type="result", payload={"done": True})
        
        assert new_p.trail_id == "trail_123"
        assert new_p.deposited_by == "worker_1"


class TestWorker:
    """Tests for Worker class."""
    
    def test_worker_with_handler(self):
        """Test creating a worker with a handler function."""
        async def my_handler(ctx: WorkerContext):
            pass
        
        worker = Worker(
            name="test_worker",
            handler=my_handler,
            reacts_to="task.created",
        )
        
        assert worker.name == "test_worker"
        assert worker.reacts_to == ["task.created"]
    
    def test_worker_reacts_to_normalization(self):
        """Test that reacts_to is normalized to a list."""
        w1 = Worker(name="w1", reacts_to="single")
        assert w1.reacts_to == ["single"]
        
        w2 = Worker(name="w2", reacts_to=["a", "b"])
        assert w2.reacts_to == ["a", "b"]
    
    @pytest.mark.asyncio
    async def test_worker_invoke_success(self):
        """Test successful worker invocation."""
        results = []
        
        async def handler(ctx: WorkerContext):
            results.append(ctx.pheromone.payload["value"])
        
        worker = Worker(name="test", handler=handler, reacts_to="test")
        board = PheromoneBoard()
        colony = Colony(name="test", board=board)
        
        ctx = WorkerContext(
            pheromone=Pheromone(type="test", payload={"value": 42}),
            board=board,
            colony=colony,
            worker_id=worker.id,
        )
        
        await worker.invoke(ctx)
        assert results == [42]
    
    @pytest.mark.asyncio
    async def test_worker_retry_on_failure(self):
        """Test worker retry logic."""
        attempts = []
        
        async def failing_handler(ctx: WorkerContext):
            attempts.append(ctx.attempt)
            if len(attempts) < 3:
                raise ValueError("Failing")
        
        worker = Worker(
            name="retry_test",
            handler=failing_handler,
            reacts_to="test",
            retry_on_failure=True,
            max_retries=3,
        )
        
        board = PheromoneBoard()
        colony = Colony(name="test", board=board)
        
        ctx = WorkerContext(
            pheromone=Pheromone(type="test", payload={}),
            board=board,
            colony=colony,
            worker_id=worker.id,
        )
        
        await worker.invoke(ctx)
        assert attempts == [0, 1, 2]
    
    @pytest.mark.asyncio
    async def test_worker_failed_pheromone(self):
        """Test that worker.failed pheromone is deposited on exhausted retries."""
        async def always_fails(ctx: WorkerContext):
            raise ValueError("Always fails")
        
        worker = Worker(
            name="failing",
            handler=always_fails,
            reacts_to="test",
            retry_on_failure=True,
            max_retries=1,
        )
        
        board = PheromoneBoard()
        colony = Colony(name="test", board=board)
        
        ctx = WorkerContext(
            pheromone=Pheromone(type="test", payload={}),
            board=board,
            colony=colony,
            worker_id=worker.id,
        )
        
        with pytest.raises(ValueError):
            await worker.invoke(ctx)
        
        # Check that worker.failed was deposited
        failures = board.read(type="worker.failed")
        assert len(failures) == 1
        assert failures[0].payload["error"] == "Always fails"
    
    @pytest.mark.asyncio
    async def test_trail_id_inheritance(self):
        """Test that deposited pheromones inherit trail_id."""
        board = PheromoneBoard()
        colony = Colony(name="test", board=board)
        
        async def handler(ctx: WorkerContext):
            ctx.deposit(type="output", payload={"done": True})
        
        worker = Worker(name="test", handler=handler, reacts_to="input")
        
        ctx = WorkerContext(
            pheromone=Pheromone(
                type="input",
                payload={},
                trail_id="trail_xyz",
            ),
            board=board,
            colony=colony,
            worker_id=worker.id,
        )
        
        await worker.invoke(ctx)
        
        outputs = board.read(type="output")
        assert len(outputs) == 1
        assert outputs[0].trail_id == "trail_xyz"
    
    @pytest.mark.asyncio
    async def test_multi_type_worker(self):
        """Test worker that reacts to multiple types."""
        results = []
        
        async def handler(ctx: WorkerContext):
            results.append(ctx.pheromone.type)
        
        worker = Worker(
            name="multi",
            handler=handler,
            reacts_to=["type_a", "type_b"],
        )
        
        assert "type_a" in worker.reacts_to
        assert "type_b" in worker.reacts_to
    
    @pytest.mark.asyncio
    async def test_max_concurrency_queue(self):
        """Test that max_concurrency queues excess invocations."""
        import asyncio
        
        execution_order = []
        
        async def slow_handler(ctx: WorkerContext):
            execution_order.append(f"start_{ctx.pheromone.payload['n']}")
            await asyncio.sleep(0.1)
            execution_order.append(f"end_{ctx.pheromone.payload['n']}")
        
        worker = Worker(
            name="slow",
            handler=slow_handler,
            reacts_to="test",
            max_concurrency=1,  # Only one at a time
        )
        
        board = PheromoneBoard()
        colony = Colony(name="test", board=board)
        
        # Create two contexts
        ctx1 = WorkerContext(
            pheromone=Pheromone(type="test", payload={"n": 1}),
            board=board,
            colony=colony,
            worker_id=worker.id,
        )
        ctx2 = WorkerContext(
            pheromone=Pheromone(type="test", payload={"n": 2}),
            board=board,
            colony=colony,
            worker_id=worker.id,
        )
        
        # Run both concurrently
        await asyncio.gather(
            worker.invoke(ctx1),
            worker.invoke(ctx2),
        )
        
        # With max_concurrency=1, second should wait for first
        # So order should be: start_1, end_1, start_2, end_2
        # (or start_2, end_2, start_1, end_1 depending on scheduling)
        assert len(execution_order) == 4
        # First start should complete before second start
        first_start_idx = next(i for i, x in enumerate(execution_order) if x.startswith("start"))
        first_end_idx = next(i for i, x in enumerate(execution_order) if x.startswith("end"))
        second_start_idx = [i for i, x in enumerate(execution_order) if x.startswith("start")][1]
        
        # The first task's end should come before second task's start
        assert first_end_idx < second_start_idx


# Run with: pytest tests/test_worker.py -v