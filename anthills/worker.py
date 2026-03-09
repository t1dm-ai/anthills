"""
Worker: An agent that reacts to pheromones on the board.

Workers are defined declaratively — they declare what signal types they
respond to, and the colony runner invokes them when matching pheromones
are deposited.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Any, TYPE_CHECKING

from .board import Pheromone, PheromoneBoard

if TYPE_CHECKING:
    from .colony import Colony


@dataclass
class WorkerContext:
    """
    Context passed to worker handlers.
    
    Attributes:
        pheromone: The triggering pheromone
        board: Read/write access to the pheromone board
        colony: Parent colony reference
        worker_id: This worker's ID
        connectors: Resolved connector instances (injected by colony)
        invocation_id: Unique ID for this specific invocation
        attempt: Retry attempt number (0 = first try)
    """
    pheromone: Pheromone
    board: PheromoneBoard
    colony: "Colony"
    worker_id: str
    connectors: dict[str, Any] = field(default_factory=dict)
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attempt: int = 0
    
    def deposit(
        self,
        type: str,
        payload: dict,
        intensity: float = 1.0,
        **kwargs,
    ) -> Pheromone:
        """
        Deposit a new pheromone, automatically inheriting the trail_id.
        
        This is the preferred way to deposit from within a worker handler.
        """
        pheromone = Pheromone(
            type=type,
            payload=payload,
            intensity=intensity,
            deposited_by=self.worker_id,
            trail_id=self.pheromone.trail_id,  # Inherit trail
            **kwargs,
        )
        return self.board.deposit(pheromone)


class Worker:
    """
    Base class for workers that react to pheromones.
    
    Can be subclassed or used with the @colony.worker decorator.
    """
    
    reacts_to: str | list[str] = []
    max_concurrency: int = 1
    retry_on_failure: bool = False
    max_retries: int = 3
    
    def __init__(
        self,
        name: str | None = None,
        handler: Callable[[WorkerContext], Awaitable[None]] | None = None,
        reacts_to: str | list[str] | None = None,
        max_concurrency: int | None = None,
        retry_on_failure: bool | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize a worker.
        
        Args:
            name: Human-readable name (defaults to class name)
            handler: Optional handler function (for decorator usage)
            reacts_to: Override class-level reacts_to
            max_concurrency: Max simultaneous invocations
            retry_on_failure: Whether to retry on exception
            max_retries: Max retry attempts
        """
        self.id = str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self._handler = handler
        self._semaphore: asyncio.Semaphore | None = None
        
        # Instance overrides
        if reacts_to is not None:
            self.reacts_to = reacts_to
        if max_concurrency is not None:
            self.max_concurrency = max_concurrency
        if retry_on_failure is not None:
            self.retry_on_failure = retry_on_failure
        if max_retries is not None:
            self.max_retries = max_retries
        
        # Normalize reacts_to to list
        if isinstance(self.reacts_to, str):
            self.reacts_to = [self.reacts_to]
    
    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create the concurrency semaphore."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)
        return self._semaphore
    
    async def handle(self, ctx: WorkerContext) -> None:
        """
        Handle a pheromone. Override this method or pass a handler function.
        
        Args:
            ctx: Worker context with pheromone, board, and colony
        """
        if self._handler:
            await self._handler(ctx)
        else:
            raise NotImplementedError(
                f"Worker '{self.name}' must override handle() or provide a handler function"
            )
    
    async def invoke(self, ctx: WorkerContext) -> None:
        """
        Invoke the worker with retry logic and concurrency control.
        
        Args:
            ctx: Worker context
        """
        async with self._get_semaphore():
            attempt = 0
            last_error: Exception | None = None
            
            while True:
                try:
                    ctx.attempt = attempt
                    await self.handle(ctx)
                    return
                except Exception as e:
                    last_error = e
                    if self.retry_on_failure and attempt < self.max_retries:
                        attempt += 1
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        # Deposit failure pheromone
                        ctx.board.deposit(Pheromone(
                            type="worker.failed",
                            payload={
                                "worker_id": self.id,
                                "worker_name": self.name,
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "pheromone_id": ctx.pheromone.id,
                                "attempts": attempt + 1,
                            },
                            deposited_by=self.id,
                            trail_id=ctx.pheromone.trail_id,
                        ))
                        raise


def worker_decorator(
    colony: "Colony",
    reacts_to: str | list[str],
    max_concurrency: int = 1,
    retry_on_failure: bool = False,
    max_retries: int = 3,
):
    """
    Decorator factory for @colony.worker(reacts_to=...).
    
    Supports both function and class decorators.
    """
    def decorator(fn_or_class: Callable | type) -> Worker:
        # Check if it's a class (subclass of Worker or has handle method)
        if isinstance(fn_or_class, type):
            if issubclass(fn_or_class, Worker):
                # It's a Worker subclass
                worker = fn_or_class(
                    name=fn_or_class.__name__,
                    reacts_to=reacts_to,
                    max_concurrency=max_concurrency,
                    retry_on_failure=retry_on_failure,
                    max_retries=max_retries,
                )
            else:
                raise TypeError(
                    f"Class {fn_or_class.__name__} must be a subclass of Worker"
                )
        else:
            # It's a function
            async def handler(ctx: WorkerContext):
                # Support both (pheromone, board) and (ctx) signatures
                import inspect
                sig = inspect.signature(fn_or_class)
                params = list(sig.parameters.keys())
                
                if len(params) == 1 and params[0] in ('ctx', 'context'):
                    await fn_or_class(ctx)
                elif len(params) >= 2:
                    # Legacy signature: (pheromone, board)
                    await fn_or_class(ctx.pheromone, ctx.board)
                else:
                    await fn_or_class(ctx)
            
            worker = Worker(
                name=fn_or_class.__name__,
                handler=handler,
                reacts_to=reacts_to,
                max_concurrency=max_concurrency,
                retry_on_failure=retry_on_failure,
                max_retries=max_retries,
            )
        
        colony.register_worker(worker)
        return worker
    
    return decorator
