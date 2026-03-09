"""
Tests for Claude integration (ClaudeWorker).

These tests mock the Anthropic client to avoid real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from anthills import Colony, Pheromone, PheromoneBoard
from anthills.worker import WorkerContext


# Mock response objects
@dataclass
class MockTextBlock:
    type: str = "text"
    text: str = "This is a response"


@dataclass 
class MockToolUseBlock:
    type: str = "tool_use"
    id: str = "tool_123"
    name: str = "search"
    input: dict = None
    
    def __post_init__(self):
        if self.input is None:
            self.input = {"query": "test"}


@dataclass
class MockResponse:
    content: list = None
    stop_reason: str = "end_turn"
    
    def __post_init__(self):
        if self.content is None:
            self.content = [MockTextBlock()]


class TestClaudeWorkerImport:
    """Test that ClaudeWorker can be imported."""
    
    def test_import_llm_worker(self):
        """LLMWorker should always be importable."""
        from anthills.integrations.claude import LLMWorker
        assert LLMWorker is not None
    
    def test_import_claude_worker(self):
        """ClaudeWorker should be importable (but may fail on use without anthropic)."""
        from anthills.integrations.claude import ClaudeWorker
        assert ClaudeWorker is not None


class TestLLMWorker:
    """Tests for the base LLMWorker class."""
    
    @pytest.mark.asyncio
    async def test_llm_worker_build_messages_default(self):
        """Test default build_messages implementation."""
        from anthills.integrations.claude import LLMWorker
        
        worker = LLMWorker(name="test", reacts_to="test")
        pheromone = Pheromone(type="test", payload={"key": "value"})
        
        messages = await worker.build_messages(pheromone)
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "key" in messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_llm_worker_parse_response_default(self):
        """Test default parse_response implementation."""
        from anthills.integrations.claude import LLMWorker
        
        worker = LLMWorker(name="test", reacts_to="test")
        pheromone = Pheromone(type="test", payload={})
        
        payload = await worker.parse_response("test response", pheromone)
        
        assert payload["result"] == "test response"
        assert payload["source_pheromone_id"] == pheromone.id


class TestClaudeWorker:
    """Tests for ClaudeWorker (with mocked Anthropic client)."""
    
    @pytest.mark.asyncio
    async def test_claude_worker_calls_api(self):
        """Test that ClaudeWorker calls the Anthropic API."""
        from anthills.integrations.claude import ClaudeWorker
        
        # Create a mock client
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=MockResponse())
        
        with patch.object(ClaudeWorker, '_get_client', return_value=mock_client):
            worker = ClaudeWorker(
                name="test",
                reacts_to="test",
            )
            worker.output_pheromone_type = "result"
            
            messages = [{"role": "user", "content": "test"}]
            response = await worker.call_llm(messages)
            
            mock_client.messages.create.assert_called_once()
            assert response.stop_reason == "end_turn"
    
    @pytest.mark.asyncio
    async def test_claude_worker_deposits_output_pheromone(self):
        """Test that ClaudeWorker deposits output pheromone."""
        from anthills.integrations.claude import ClaudeWorker
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=MockResponse())
        
        with patch.object(ClaudeWorker, '_get_client', return_value=mock_client):
            board = PheromoneBoard()
            colony = Colony(name="test", board=board)
            
            worker = ClaudeWorker(
                name="test_worker",
                reacts_to="input",
            )
            worker.output_pheromone_type = "output"
            
            ctx = WorkerContext(
                pheromone=Pheromone(type="input", payload={"data": "test"}),
                board=board,
                colony=colony,
                worker_id=worker.id,
            )
            
            await worker.handle(ctx)
            
            # Check output pheromone was deposited
            outputs = board.read(type="output")
            assert len(outputs) == 1
            assert "result" in outputs[0].payload
    
    @pytest.mark.asyncio
    async def test_claude_worker_trail_id_propagated(self):
        """Test that output pheromone inherits trail_id."""
        from anthills.integrations.claude import ClaudeWorker
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=MockResponse())
        
        with patch.object(ClaudeWorker, '_get_client', return_value=mock_client):
            board = PheromoneBoard()
            colony = Colony(name="test", board=board)
            
            worker = ClaudeWorker(name="test", reacts_to="input")
            worker.output_pheromone_type = "output"
            
            ctx = WorkerContext(
                pheromone=Pheromone(
                    type="input",
                    payload={},
                    trail_id="trail_abc123",
                ),
                board=board,
                colony=colony,
                worker_id=worker.id,
            )
            
            await worker.handle(ctx)
            
            outputs = board.read(type="output")
            assert outputs[0].trail_id == "trail_abc123"
    
    @pytest.mark.asyncio
    async def test_claude_worker_custom_build_messages(self):
        """Test that custom build_messages is used."""
        from anthills.integrations.claude import ClaudeWorker
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=MockResponse())
        
        class CustomWorker(ClaudeWorker):
            async def build_messages(self, pheromone):
                return [{"role": "user", "content": f"Custom: {pheromone.payload['topic']}"}]
        
        with patch.object(ClaudeWorker, '_get_client', return_value=mock_client):
            worker = CustomWorker(name="custom", reacts_to="test")
            
            pheromone = Pheromone(type="test", payload={"topic": "AI"})
            messages = await worker.build_messages(pheromone)
            
            assert "Custom: AI" in messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_claude_worker_tool_use_response(self):
        """Test handling of tool_use response blocks."""
        from anthills.integrations.claude import ClaudeWorker
        
        response_with_tools = MockResponse(
            content=[
                MockTextBlock(text="I'll search for that"),
                MockToolUseBlock(name="search", input={"query": "test"}),
            ],
            stop_reason="tool_use",
        )
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=response_with_tools)
        
        with patch.object(ClaudeWorker, '_get_client', return_value=mock_client):
            worker = ClaudeWorker(name="test", reacts_to="test")
            
            pheromone = Pheromone(type="test", payload={})
            payload = await worker.parse_response(response_with_tools, pheromone)
            
            assert payload["result"] == "I'll search for that"
            assert len(payload["tool_calls"]) == 1
            assert payload["tool_calls"][0]["name"] == "search"
            assert payload["stop_reason"] == "tool_use"


class TestClaudeToolWorker:
    """Tests for ClaudeToolWorker with tool execution loop."""
    
    @pytest.mark.asyncio
    async def test_tool_worker_executes_tools(self):
        """Test that tool worker executes tools and continues."""
        from anthills.integrations.claude import ClaudeToolWorker
        
        # First response requests a tool
        response1 = MockResponse(
            content=[MockToolUseBlock(name="search", input={"query": "test"})],
            stop_reason="tool_use",
        )
        # Second response is final
        response2 = MockResponse(
            content=[MockTextBlock(text="Final answer")],
            stop_reason="end_turn",
        )
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=[response1, response2])
        
        async def mock_search(query: str) -> str:
            return f"Results for: {query}"
        
        with patch.object(ClaudeToolWorker, '_get_client', return_value=mock_client):
            board = PheromoneBoard()
            colony = Colony(name="test", board=board)
            
            worker = ClaudeToolWorker(name="test", reacts_to="test")
            worker.output_pheromone_type = "result"
            worker.tool_handlers = {"search": mock_search}
            
            ctx = WorkerContext(
                pheromone=Pheromone(type="test", payload={}),
                board=board,
                colony=colony,
                worker_id=worker.id,
            )
            
            await worker.handle(ctx)
            
            # Should have called API twice
            assert mock_client.messages.create.call_count == 2
            
            # Should have deposited final result
            results = board.read(type="result")
            assert len(results) == 1
            assert results[0].payload["result"] == "Final answer"


# Run with: pytest tests/test_claude_integration.py -v
