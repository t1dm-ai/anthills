"""
Connector Registry: Resolves and manages connector instances.

The registry maps connector_type → ConnectorInstance for a given colony run.
It resolves configs from storage and initializes live clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    Connector,
    ConnectorConfig,
    ConnectorNotConfiguredError,
    ConnectorNotFoundError,
)

if TYPE_CHECKING:
    pass


class ConnectorRegistry:
    """
    Manages connector configs and instances for a colony.
    
    Responsibilities:
    - Register connector implementation classes
    - Store user connector configs (credentials)
    - Resolve configs to live, authenticated connector instances
    - Health check all connectors
    - Clean up on shutdown
    
    Example:
        registry = ConnectorRegistry()
        
        # Register connector classes
        registry.register_class(GmailConnector)
        registry.register_class(SlackConnector)
        
        # Add user credentials
        registry.add_config(ConnectorConfig(
            connector_type="gmail",
            credentials={"access_token": "..."},
            owner_id="user_123",
        ))
        
        # Resolve to live instance
        gmail = await registry.resolve("gmail")
        await gmail.send_email(...)
    """
    
    def __init__(self):
        self._configs: dict[str, ConnectorConfig] = {}
        self._instances: dict[str, Connector] = {}
        self._connector_classes: dict[str, type[Connector]] = {}
    
    def register_class(self, connector_cls: type[Connector]) -> None:
        """
        Register a connector implementation class.
        
        Args:
            connector_cls: A Connector subclass with connector_type set
        """
        if not connector_cls.connector_type:
            raise ValueError(
                f"Connector class {connector_cls.__name__} must set connector_type"
            )
        self._connector_classes[connector_cls.connector_type] = connector_cls
    
    def add_config(self, config: ConnectorConfig) -> None:
        """
        Add user credentials for a connector type.
        
        Args:
            config: ConnectorConfig with credentials and settings
        """
        self._configs[config.connector_type] = config
    
    def has_config(self, connector_type: str) -> bool:
        """Check if config exists for a connector type."""
        return connector_type in self._configs
    
    def has_class(self, connector_type: str) -> bool:
        """Check if a connector class is registered for a type."""
        return connector_type in self._connector_classes
    
    async def resolve(self, connector_type: str) -> Connector:
        """
        Return a live, authenticated connector instance.
        
        If already resolved, returns cached instance. Otherwise:
        1. Looks up config for connector_type
        2. Looks up connector class implementation
        3. Instantiates and calls connect()
        4. Caches and returns the instance
        
        Args:
            connector_type: e.g. "gmail", "slack"
            
        Returns:
            Authenticated Connector instance
            
        Raises:
            ConnectorNotConfiguredError: If no config for this connector
            ConnectorNotFoundError: If no implementation class registered
        """
        # Return cached instance if available
        if connector_type in self._instances:
            return self._instances[connector_type]
        
        # Look up config
        config = self._configs.get(connector_type)
        if not config:
            raise ConnectorNotConfiguredError(
                f"Connector '{connector_type}' is required but not configured. "
                f"Connect your {connector_type} account to use this agent."
            )
        
        # Look up implementation class
        cls = self._connector_classes.get(connector_type)
        if not cls:
            raise ConnectorNotFoundError(
                f"No connector implementation for '{connector_type}'. "
                f"Make sure to register the connector class with the registry."
            )
        
        # Instantiate and connect
        instance = cls(config)
        await instance.connect()
        
        # Cache and return
        self._instances[connector_type] = instance
        return instance
    
    async def resolve_many(self, types: list[str]) -> dict[str, Connector]:
        """
        Resolve multiple connector types at once.
        
        Args:
            types: List of connector types to resolve
            
        Returns:
            Dict mapping connector_type → Connector instance
        """
        result = {}
        for t in types:
            result[t] = await self.resolve(t)
        return result
    
    async def health_check_all(self) -> dict[str, bool]:
        """
        Health check all instantiated connectors.
        
        Returns:
            Dict mapping connector_type → health status
        """
        results = {}
        for connector_type, instance in self._instances.items():
            try:
                results[connector_type] = await instance.health_check()
            except Exception:
                results[connector_type] = False
        return results
    
    async def disconnect_all(self) -> None:
        """
        Disconnect all connector instances.
        
        Called when colony stops to clean up resources.
        """
        for instance in self._instances.values():
            try:
                await instance.disconnect()
            except Exception:
                pass  # Best effort cleanup
        self._instances.clear()
    
    def list_configured(self) -> list[str]:
        """List connector types that have configs added."""
        return list(self._configs.keys())
    
    def list_registered(self) -> list[str]:
        """List connector types that have classes registered."""
        return list(self._connector_classes.keys())


def requires(*connector_types: str) -> list[str]:
    """
    Declare connector dependencies for a worker.
    
    Usage:
        class MyWorker(Worker):
            connectors = requires("gmail", "slack")
    
    Args:
        connector_types: Connector type strings
        
    Returns:
        List of connector type strings (for use in worker declaration)
    """
    return list(connector_types)
