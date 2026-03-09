"""
Tests for the Connector system.

Tests cover:
- ConnectorConfig data structure
- Connector base class
- ConnectorRegistry resolution and caching
- Worker connector injection
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from anthills.connectors import (
    Connector,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectorNotConfiguredError,
    ConnectorNotFoundError,
    requires,
)
from anthills import Colony, Worker, Pheromone, PheromoneBoard
from anthills.worker import WorkerContext


# Test connector implementation
class MockConnector(Connector):
    """Test connector for unit tests."""
    
    connector_type = "mock"
    display_name = "Mock Connector"
    description = "A mock connector for testing"
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.connect_called = False
        self.disconnect_called = False
        self.health_check_result = True
    
    async def connect(self) -> None:
        self.connect_called = True
        self._client = "mock_client"
    
    async def health_check(self) -> bool:
        return self.health_check_result
    
    async def disconnect(self) -> None:
        self.disconnect_called = True
        self._client = None
    
    async def do_something(self) -> str:
        return "done"


class TestConnectorConfig:
    """Tests for ConnectorConfig dataclass."""
    
    def test_connector_config_creation(self):
        """Test creating a connector config."""
        config = ConnectorConfig(
            connector_type="gmail",
            credentials={"access_token": "abc123"},
            settings={"default_from": "test@example.com"},
            owner_id="user_123",
        )
        
        assert config.connector_type == "gmail"
        assert config.credentials["access_token"] == "abc123"
        assert config.settings["default_from"] == "test@example.com"
        assert config.owner_id == "user_123"
    
    def test_connector_config_defaults(self):
        """Test connector config default values."""
        config = ConnectorConfig(connector_type="slack")
        
        assert config.connector_type == "slack"
        assert config.credentials == {}
        assert config.settings == {}
        assert config.owner_id == ""


class TestConnector:
    """Tests for Connector base class."""
    
    @pytest.mark.asyncio
    async def test_connector_connect(self):
        """Test connector connect method."""
        config = ConnectorConfig(connector_type="mock")
        connector = MockConnector(config)
        
        assert not connector.is_connected
        await connector.connect()
        assert connector.is_connected
        assert connector.connect_called
    
    @pytest.mark.asyncio
    async def test_connector_health_check(self):
        """Test connector health check."""
        config = ConnectorConfig(connector_type="mock")
        connector = MockConnector(config)
        
        await connector.connect()
        
        assert await connector.health_check() is True
        
        connector.health_check_result = False
        assert await connector.health_check() is False
    
    @pytest.mark.asyncio
    async def test_connector_disconnect(self):
        """Test connector disconnect."""
        config = ConnectorConfig(connector_type="mock")
        connector = MockConnector(config)
        
        await connector.connect()
        assert connector.is_connected
        
        await connector.disconnect()
        assert not connector.is_connected
        assert connector.disconnect_called


class TestConnectorRegistry:
    """Tests for ConnectorRegistry."""
    
    def test_register_class(self):
        """Test registering a connector class."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        
        assert registry.has_class("mock")
        assert "mock" in registry.list_registered()
    
    def test_register_class_without_type_raises(self):
        """Test that registering a class without connector_type raises."""
        class BadConnector(Connector):
            connector_type = ""  # Empty
            async def connect(self): pass
            async def health_check(self): return True
        
        registry = ConnectorRegistry()
        with pytest.raises(ValueError, match="must set connector_type"):
            registry.register_class(BadConnector)
    
    def test_add_config(self):
        """Test adding a connector config."""
        registry = ConnectorRegistry()
        
        config = ConnectorConfig(
            connector_type="mock",
            credentials={"token": "abc"},
            owner_id="user_1",
        )
        registry.add_config(config)
        
        assert registry.has_config("mock")
        assert "mock" in registry.list_configured()
    
    @pytest.mark.asyncio
    async def test_resolve_connector(self):
        """Test resolving a connector to a live instance."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        registry.add_config(ConnectorConfig(
            connector_type="mock",
            credentials={"token": "abc"},
        ))
        
        connector = await registry.resolve("mock")
        
        assert isinstance(connector, MockConnector)
        assert connector.is_connected
        assert connector.connect_called
    
    @pytest.mark.asyncio
    async def test_resolve_caches_instance(self):
        """Test that resolve returns cached instance on subsequent calls."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        registry.add_config(ConnectorConfig(connector_type="mock"))
        
        connector1 = await registry.resolve("mock")
        connector2 = await registry.resolve("mock")
        
        assert connector1 is connector2
    
    @pytest.mark.asyncio
    async def test_resolve_without_config_raises(self):
        """Test that resolving without config raises ConnectorNotConfiguredError."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        
        with pytest.raises(ConnectorNotConfiguredError) as exc_info:
            await registry.resolve("mock")
        
        assert "not configured" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_resolve_without_class_raises(self):
        """Test that resolving without class raises ConnectorNotFoundError."""
        registry = ConnectorRegistry()
        registry.add_config(ConnectorConfig(connector_type="unknown"))
        
        with pytest.raises(ConnectorNotFoundError) as exc_info:
            await registry.resolve("unknown")
        
        assert "No connector implementation" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_resolve_many(self):
        """Test resolving multiple connectors at once."""
        registry = ConnectorRegistry()
        
        # Create two mock connector types
        class MockConnector2(MockConnector):
            connector_type = "mock2"
        
        registry.register_class(MockConnector)
        registry.register_class(MockConnector2)
        registry.add_config(ConnectorConfig(connector_type="mock"))
        registry.add_config(ConnectorConfig(connector_type="mock2"))
        
        connectors = await registry.resolve_many(["mock", "mock2"])
        
        assert len(connectors) == 2
        assert "mock" in connectors
        assert "mock2" in connectors
        assert isinstance(connectors["mock"], MockConnector)
    
    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health checking all connectors."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        registry.add_config(ConnectorConfig(connector_type="mock"))
        
        await registry.resolve("mock")
        
        health = await registry.health_check_all()
        
        assert health["mock"] is True
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self):
        """Test disconnecting all connectors."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        registry.add_config(ConnectorConfig(connector_type="mock"))
        
        connector = await registry.resolve("mock")
        assert connector.is_connected
        
        await registry.disconnect_all()
        
        assert connector.disconnect_called


class TestRequiresHelper:
    """Tests for the requires() helper function."""
    
    def test_requires_single(self):
        """Test requires with single connector."""
        result = requires("gmail")
        assert result == ["gmail"]
    
    def test_requires_multiple(self):
        """Test requires with multiple connectors."""
        result = requires("gmail", "slack", "shopify")
        assert result == ["gmail", "slack", "shopify"]


class TestWorkerConnectorInjection:
    """Tests for connector injection into workers."""
    
    @pytest.mark.asyncio
    async def test_connectors_in_worker_context(self):
        """Test that connectors are available in WorkerContext."""
        registry = ConnectorRegistry()
        registry.register_class(MockConnector)
        registry.add_config(ConnectorConfig(connector_type="mock"))
        
        board = PheromoneBoard()
        colony = Colony(
            name="test",
            board=board,
            connector_registry=registry,
            auto_halt=True,
            idle_timeout=1,
        )
        
        received_connectors = {}
        
        @colony.worker(reacts_to="test")
        async def worker_with_connector(ctx):
            received_connectors.update(ctx.connectors)
        
        # Set connectors attribute on the worker
        colony._workers[0].connectors = ["mock"]
        
        colony.deposit(type="test", payload={})
        await colony.run_async()
        
        assert "mock" in received_connectors
        assert isinstance(received_connectors["mock"], MockConnector)
    
    def test_worker_can_declare_connectors(self):
        """Test that workers can declare connector dependencies."""
        class MyWorker(Worker):
            reacts_to = "email.received"
            connectors = requires("gmail", "anthropic")
            
            async def handle(self, ctx: WorkerContext):
                pass
        
        worker = MyWorker(name="test")
        assert worker.connectors == ["gmail", "anthropic"]


class TestConnectorNotConfiguredError:
    """Tests for ConnectorNotConfiguredError message."""
    
    def test_error_message_is_user_friendly(self):
        """Test that error message is suitable for end users."""
        error = ConnectorNotConfiguredError(
            "This agent needs access to your Gmail account to respond to "
            "customer emails. Connect Gmail to continue."
        )
        
        message = str(error)
        assert "Gmail" in message
        assert "Connect" in message


# Run with: pytest tests/test_connectors.py -v
