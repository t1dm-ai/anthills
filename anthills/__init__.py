"""
Anthills: Stigmergy-based AI agent orchestration.

Agents coordinate through a shared pheromone board — not a central planner.
Complex, adaptive behavior emerges from simple local rules.
"""

from .board import Pheromone, PheromoneBoard, BoardEvent
from .worker import Worker, WorkerContext
from .colony import Colony
from .connectors import (
    Connector,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectorNotConfiguredError,
    ConnectorNotFoundError,
    requires,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "Colony",
    "Worker",
    "WorkerContext",
    "Pheromone",
    "PheromoneBoard",
    "BoardEvent",
    # Connectors
    "Connector",
    "ConnectorConfig",
    "ConnectorRegistry",
    "ConnectorNotConfiguredError",
    "ConnectorNotFoundError",
    "requires",
]
