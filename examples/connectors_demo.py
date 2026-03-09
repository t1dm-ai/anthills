#!/usr/bin/env python3
"""
Demonstration of Connectors in Anthills.

This example shows how to:
1. Create custom connectors
2. Use the ConnectorRegistry
3. Inject connectors into workers via Colony
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from anthills import Colony, Pheromone
from anthills.connectors import (
    Connector,
    ConnectorConfig,
    ConnectorRegistry,
    requires,
    ConnectorError,
)


# =============================================================================
# CUSTOM CONNECTOR EXAMPLE: Mock Database
# =============================================================================

@dataclass
class DatabaseConfig(ConnectorConfig):
    """Configuration for the mock database connector."""
    host: str = "localhost"
    port: int = 5432
    database: str = "anthills_demo"


class DatabaseConnector(Connector[DatabaseConfig]):
    """
    A mock database connector for demonstration.
    
    In a real implementation, this would connect to PostgreSQL, MySQL, etc.
    """
    
    name = "database"
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        super().__init__(config or DatabaseConfig())
        self._connected = False
        self._data: dict = {}  # Mock in-memory storage
    
    async def connect(self) -> None:
        """Establish database connection."""
        print(f"🔌 Connecting to database at {self.config.host}:{self.config.port}")
        await asyncio.sleep(0.1)  # Simulate connection time
        self._connected = True
        print(f"✅ Connected to '{self.config.database}'")
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self._connected:
            print("🔌 Disconnecting from database...")
            self._connected = False
    
    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        return self._connected
    
    # Mock database operations
    async def insert(self, table: str, data: dict) -> str:
        """Insert a record into a table."""
        if not self._connected:
            raise ConnectorError("Not connected to database")
        
        record_id = f"{table}_{len(self._data)}"
        self._data[record_id] = {"table": table, **data}
        print(f"📝 Inserted into {table}: {data}")
        return record_id
    
    async def query(self, table: str) -> list:
        """Query all records from a table."""
        if not self._connected:
            raise ConnectorError("Not connected to database")
        
        return [v for k, v in self._data.items() if v.get("table") == table]


# =============================================================================
# CUSTOM CONNECTOR EXAMPLE: Mock HTTP API
# =============================================================================

@dataclass
class APIConfig(ConnectorConfig):
    """Configuration for the mock API connector."""
    base_url: str = "https://api.example.com"
    api_key: str = ""
    timeout: int = 30


class APIConnector(Connector[APIConfig]):
    """
    A mock HTTP API connector for demonstration.
    
    In a real implementation, this would use aiohttp or httpx.
    """
    
    name = "api"
    
    async def connect(self) -> None:
        print(f"🌐 Initializing API client for {self.config.base_url}")
    
    async def disconnect(self) -> None:
        print("🌐 Closing API client")
    
    async def get(self, endpoint: str) -> dict:
        """Make a GET request."""
        print(f"📡 GET {self.config.base_url}/{endpoint}")
        # Mock response
        return {"status": "ok", "endpoint": endpoint, "data": {"demo": True}}
    
    async def post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request."""
        print(f"📡 POST {self.config.base_url}/{endpoint} with {data}")
        return {"status": "created", "id": "123"}


# =============================================================================
# DEMO: Using connectors with a Colony
# =============================================================================

async def run_connector_demo():
    """Demonstrate using connectors in a colony."""
    print("=" * 60)
    print("ANTHILLS CONNECTORS DEMO")
    print("=" * 60)
    
    # 1. Create connector instances
    db_connector = DatabaseConnector(DatabaseConfig(
        host="localhost",
        port=5432,
        database="demo_db"
    ))
    
    api_connector = APIConnector(APIConfig(
        base_url="https://api.example.com",
        api_key="demo-key-123"
    ))
    
    # 2. Create registry and register connectors
    registry = ConnectorRegistry()
    registry.register(db_connector)
    registry.register(api_connector)
    
    print(f"\n📋 Registered connectors: {registry.list_connectors()}")
    
    # 3. Create colony with connector registry
    colony = Colony(name="connector-demo", connectors=registry)
    
    # 4. Define workers that use connectors
    @colony.worker(reacts_to="user.created", requires=["database"])
    async def save_user(ctx):
        """Save a new user to the database."""
        db = ctx.connectors["database"]
        user_data = ctx.pheromone.payload
        
        record_id = await db.insert("users", user_data)
        
        await ctx.board.deposit(Pheromone(
            type="user.saved",
            payload={"record_id": record_id, **user_data},
            deposited_by="save_user",
        ))
    
    @colony.worker(reacts_to="user.saved", requires=["api"])
    async def notify_external_service(ctx):
        """Notify an external service about the new user."""
        api = ctx.connectors["api"]
        user_data = ctx.pheromone.payload
        
        response = await api.post("webhooks/user-created", {
            "user_id": user_data["record_id"],
            "email": user_data.get("email"),
        })
        
        await ctx.board.deposit(Pheromone(
            type="notification.sent",
            payload={"api_response": response},
            deposited_by="notify_external_service",
        ))
    
    @colony.worker(reacts_to="user.saved", requires=["database"])
    async def create_welcome_task(ctx):
        """Create a welcome task for the new user."""
        db = ctx.connectors["database"]
        user_data = ctx.pheromone.payload
        
        await db.insert("tasks", {
            "type": "send_welcome_email",
            "user_id": user_data["record_id"],
            "status": "pending",
        })
        
        await ctx.board.deposit(Pheromone(
            type="task.created",
            payload={"task_type": "send_welcome_email"},
            deposited_by="create_welcome_task",
        ))
    
    @colony.worker(reacts_to="notification.sent")
    async def log_notification(ctx):
        """Log that notification was sent."""
        print(f"📧 Notification logged: {ctx.pheromone.payload}")
    
    @colony.worker(reacts_to="task.created")
    async def log_task(ctx):
        """Log that task was created."""
        print(f"📋 Task logged: {ctx.pheromone.payload}")
    
    # 5. Trigger the workflow
    print("\n🚀 Starting workflow...")
    colony.deposit(
        type="user.created",
        payload={
            "email": "alice@example.com",
            "name": "Alice Smith",
            "plan": "premium",
        },
    )
    
    # 6. Run the colony
    await colony.run(auto_halt=True)
    
    print("\n✅ Workflow complete!")
    print("=" * 60)


# =============================================================================
# DEMO: Connector lifecycle and health checks
# =============================================================================

async def run_lifecycle_demo():
    """Demonstrate connector lifecycle management."""
    print("\n" + "=" * 60)
    print("CONNECTOR LIFECYCLE DEMO")
    print("=" * 60)
    
    db = DatabaseConnector()
    
    # Check health before connecting
    print(f"\n🏥 Health check (before connect): {await db.health_check()}")
    
    # Connect
    await db.connect()
    
    # Check health after connecting
    print(f"🏥 Health check (after connect): {await db.health_check()}")
    
    # Use the connector
    await db.insert("demo", {"key": "value"})
    results = await db.query("demo")
    print(f"🔍 Query results: {results}")
    
    # Disconnect
    await db.disconnect()
    print(f"🏥 Health check (after disconnect): {await db.health_check()}")


# =============================================================================
# DEMO: Registry features
# =============================================================================

def run_registry_demo():
    """Demonstrate registry features."""
    print("\n" + "=" * 60)
    print("CONNECTOR REGISTRY DEMO")
    print("=" * 60)
    
    registry = ConnectorRegistry()
    
    # Register connectors
    registry.register(DatabaseConnector())
    registry.register(APIConnector())
    
    print(f"\n📋 Connectors: {registry.list_connectors()}")
    
    # Get a specific connector
    db = registry.get("database")
    print(f"🔌 Got database connector: {db.name}")
    
    # Try to get non-existent connector
    try:
        registry.get("nonexistent")
    except KeyError as e:
        print(f"❌ Expected error: {e}")
    
    # Check for connector existence
    print(f"\n🔍 Has 'database': {registry.has('database')}")
    print(f"🔍 Has 'redis': {registry.has('redis')}")
    
    # Resolve requirements
    requirements = ["database", "api"]
    resolved = registry.resolve(requirements)
    print(f"\n✅ Resolved {requirements}: {list(resolved.keys())}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all demonstrations."""
    print("\n🐜 ANTHILLS CONNECTORS DEMO 🐜\n")
    
    # Registry features (sync)
    run_registry_demo()
    
    # Lifecycle demo (async)
    asyncio.run(run_lifecycle_demo())
    
    # Full colony demo (async)
    asyncio.run(run_connector_demo())
    
    print("\n🏁 All demos complete!")


if __name__ == "__main__":
    main()
