"""
Colony: The top-level orchestration object.

The Colony holds the pheromone board, the worker registry, and the async
event loop that connects deposits to worker invocations. It is the main
public API surface for Anthills.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Callable, Any

from .board import Pheromone, PheromoneBoard
from .worker import Worker, WorkerContext, worker_decorator
from .connectors import ConnectorRegistry


class Colony:
    """
    A named group of workers sharing a pheromone board.
    
    The Colony:
    - Manages the pheromone board
    - Registers workers and routes pheromones to them
    - Manages connectors for external tool integrations
    - Provides the async event loop for execution
    - Exposes the ledger for auditing and replay
    """
    
    def __init__(
        self,
        name: str,
        board: PheromoneBoard | None = None,
        connector_registry: ConnectorRegistry | None = None,
        auto_halt: bool = True,
        idle_timeout: int = 5,
        evaporation_interval: int = 10,
    ):
        """
        Initialize a colony.
        
        Args:
            name: Colony identifier
            board: Pheromone board instance (defaults to PheromoneBoard)
            connector_registry: Registry for external connectors
            auto_halt: Stop when board goes quiet
            idle_timeout: Seconds of quiet before halt
            evaporation_interval: Seconds between evaporation ticks
        """
        self.name = name
        self.id = str(uuid.uuid4())
        self._board = board or PheromoneBoard()
        self._connector_registry = connector_registry or ConnectorRegistry()
        self._workers: list[Worker] = []
        self._auto_halt = auto_halt
        self._idle_timeout = idle_timeout
        self._evaporation_interval = evaporation_interval
        self._running = False
        self._active_tasks: set[asyncio.Task] = set()
        self._pending_pheromones: list[Pheromone] = []
    
    @property
    def board(self) -> PheromoneBoard:
        """Access the pheromone board."""
        return self._board
    
    @property
    def connectors(self) -> ConnectorRegistry:
        """Access the connector registry."""
        return self._connector_registry
    
    def events(self) -> list:
        """Get the full event ledger."""
        return self._board.events()
    
    def replay(self, as_of):
        """Replay board state at a specific timestamp."""
        return self._board.replay(as_of)
    
    def worker(
        self,
        reacts_to: str | list[str],
        max_concurrency: int = 1,
        retry_on_failure: bool = False,
        max_retries: int = 3,
    ) -> Callable:
        """
        Decorator to register a worker.
        
        Usage:
            @colony.worker(reacts_to="task.created")
            async def my_worker(pheromone, board):
                ...
        
        Args:
            reacts_to: Pheromone type(s) this worker responds to
            max_concurrency: Max simultaneous invocations
            retry_on_failure: Whether to retry on exception
            max_retries: Max retry attempts
            
        Returns:
            Decorator function
        """
        return worker_decorator(
            colony=self,
            reacts_to=reacts_to,
            max_concurrency=max_concurrency,
            retry_on_failure=retry_on_failure,
            max_retries=max_retries,
        )
    
    def register_worker(self, worker: Worker) -> None:
        """
        Register a worker with the colony.
        
        Sets up subscriptions for the worker's reacts_to types.
        
        Args:
            worker: The worker to register
        """
        self._workers.append(worker)
        
        # Subscribe to each type the worker reacts to
        types = worker.reacts_to if isinstance(worker.reacts_to, list) else [worker.reacts_to]
        for t in types:
            self._board.subscribe(t, lambda p, w=worker: self._dispatch(w, p))
    
    def deposit(
        self,
        type: str,
        payload: dict,
        intensity: float = 1.0,
        trail_id: str | None = None,
        ttl_seconds: int | None = None,
        **kwargs,
    ) -> Pheromone:
        """
        Deposit a pheromone onto the board.
        
        Args:
            type: Pheromone type (e.g., 'task.created')
            payload: Arbitrary data
            intensity: Signal strength (0.0-1.0)
            trail_id: Optional trail ID (auto-generated if None)
            ttl_seconds: Time-to-live
            **kwargs: Additional pheromone fields
            
        Returns:
            The deposited pheromone
        """
        pheromone = Pheromone(
            type=type,
            payload=payload,
            intensity=intensity,
            deposited_by="colony",
            trail_id=trail_id or str(uuid.uuid4()),
            ttl_seconds=ttl_seconds,
            **kwargs,
        )
        
        # If not running, queue for later
        if not self._running:
            self._pending_pheromones.append(pheromone)
        
        return self._board.deposit(pheromone)
    
    def _dispatch(self, worker: Worker, pheromone: Pheromone) -> None:
        """
        Dispatch a pheromone to a worker.
        
        Creates an async task for the worker invocation.
        """
        if not self._running:
            return  # Don't dispatch until running
        
        task = asyncio.ensure_future(self._invoke_worker_with_connectors(worker, pheromone))
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))
    
    async def _invoke_worker_with_connectors(
        self, worker: Worker, pheromone: Pheromone
    ) -> None:
        """Resolve connectors and invoke a worker."""
        # Resolve required connectors
        required = getattr(worker, "connectors", [])
        resolved = await self._connector_registry.resolve_many(required) if required else {}
        
        ctx = WorkerContext(
            pheromone=pheromone,
            board=self._board,
            colony=self,
            worker_id=worker.id,
            connectors=resolved,
        )
        
        try:
            await worker.invoke(ctx)
        except Exception as e:
            # Error already logged via worker.failed pheromone
            pass
    
    async def run_async(self) -> None:
        """
        Run the colony asynchronously.
        
        Starts the evaporation ticker, drains pending pheromones,
        and routes new deposits to workers until idle.
        """
        self._running = True
        
        # Start evaporation ticker
        evap_task = asyncio.create_task(self._evaporation_loop())
        
        # Drain any pre-deposited pheromones
        await self._drain_pending()
        
        # Wait for idle or explicit stop
        if self._auto_halt:
            await self._idle_monitor()
        else:
            # Run forever until stop() is called
            while self._running:
                await asyncio.sleep(0.1)
        
        # Cleanup
        evap_task.cancel()
        try:
            await evap_task
        except asyncio.CancelledError:
            pass
        
        # Wait for in-flight tasks
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        # Disconnect all connectors
        await self._connector_registry.disconnect_all()
        
        self._running = False
    
    def run(self) -> None:
        """
        Run the colony synchronously.
        
        Blocks until the colony stops. If already in an async context,
        use `await colony.run_async()` instead.
        """
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - can't use asyncio.run()
            raise RuntimeError(
                "colony.run() cannot be called from async context. "
                "Use 'await colony.run_async()' instead."
            )
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            asyncio.run(self.run_async())
    
    def stop(self) -> None:
        """
        Stop the colony gracefully.
        
        Waits for in-flight handlers to complete.
        """
        self._running = False
    
    async def _drain_pending(self) -> None:
        """Process pheromones deposited before run() was called."""
        # Re-dispatch pending pheromones to trigger subscriptions
        for pheromone in self._pending_pheromones:
            for worker in self._workers:
                types = worker.reacts_to if isinstance(worker.reacts_to, list) else [worker.reacts_to]
                if pheromone.type in types:
                    self._dispatch(worker, pheromone)
        
        self._pending_pheromones.clear()
        
        # Give tasks a chance to start
        await asyncio.sleep(0)
    
    async def _evaporation_loop(self) -> None:
        """Background task that periodically evaporates expired pheromones."""
        while self._running:
            await asyncio.sleep(self._evaporation_interval)
            self._board.evaporate()
    
    async def _idle_monitor(self) -> None:
        """Monitor for idle state and stop when reached."""
        idle_for = 0
        while self._running:
            await asyncio.sleep(1)
            if not self._active_tasks:
                idle_for += 1
                if idle_for >= self._idle_timeout:
                    self.stop()
            else:
                idle_for = 0
