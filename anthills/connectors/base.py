"""
Connector Base: Abstract interface and data structures for connectors.

A Connector is a named, injectable abstraction over an external tool or service.
Workers declare which connectors they need; the colony runner injects them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorConfig:
    """
    User-supplied credentials and settings for a connector.
    
    Attributes:
        connector_type: e.g. "gmail", "slack", "shopify"
        credentials: OAuth tokens, API keys, etc. — never logged
        settings: Non-sensitive config (e.g. default_from_email)
        owner_id: User/org who owns these credentials
    """
    connector_type: str
    credentials: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    owner_id: str = ""


class Connector(ABC):
    """
    Base class for all external tool connectors.
    
    Subclasses must:
    - Set `connector_type` class attribute
    - Implement `connect()` and `health_check()`
    - Expose domain-specific methods (e.g. GmailConnector.send_email())
    
    Example:
        class GmailConnector(Connector):
            connector_type = "gmail"
            display_name = "Gmail"
            
            async def connect(self):
                # Initialize authenticated client
                ...
            
            async def health_check(self) -> bool:
                # Verify connection is live
                ...
            
            async def send_email(self, to: str, subject: str, body: str):
                # Domain-specific method
                ...
    """
    
    connector_type: str = ""           # Must be set by subclass
    display_name: str = ""             # Human-readable: "Gmail", "Slack", etc.
    description: str = ""              # Shown in SMB agent catalog
    required_scopes: list[str] = []    # OAuth scopes needed
    
    def __init__(self, config: ConnectorConfig):
        """
        Initialize connector with user config.
        
        Args:
            config: User credentials and settings
        """
        self.config = config
        self._client: Any = None
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Initialize and authenticate the client.
        
        Called by ConnectorRegistry.resolve() before the connector
        is injected into a worker context.
        """
        ...
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify the connection is live and credentials are valid.
        
        Returns:
            True if connector is healthy, False otherwise
        """
        ...
    
    async def disconnect(self) -> None:
        """
        Optional cleanup on connector shutdown.
        
        Called when the colony stops or connector is no longer needed.
        """
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if connect() has been called successfully."""
        return self._client is not None


class ConnectorNotConfiguredError(Exception):
    """
    Raised when a worker needs a connector the user hasn't set up yet.
    
    This error surfaces as a friendly onboarding prompt in the SMB UI:
    "This agent needs access to your Gmail. Connect it here →"
    
    The error message IS the user-facing prompt — write it accordingly.
    
    Example:
        raise ConnectorNotConfiguredError(
            "This agent needs access to your Gmail account to respond to "
            "customer emails. Connect Gmail to continue."
        )
    """
    pass


class ConnectorNotFoundError(Exception):
    """
    Raised when no implementation exists for a connector type.
    
    This typically means a worker requires a connector that hasn't
    been registered with the ConnectorRegistry.
    """
    pass
