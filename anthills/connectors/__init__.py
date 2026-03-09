"""
Anthills Connectors: External tool integrations.

Connectors provide a standard abstraction over external services (Gmail, Slack, etc.).
Workers declare connector dependencies; the colony runner injects authenticated instances.
"""

from .base import (
    Connector,
    ConnectorConfig,
    ConnectorNotConfiguredError,
    ConnectorNotFoundError,
)
from .registry import ConnectorRegistry, requires

__all__ = [
    "Connector",
    "ConnectorConfig",
    "ConnectorRegistry",
    "ConnectorNotConfiguredError",
    "ConnectorNotFoundError",
    "requires",
]
