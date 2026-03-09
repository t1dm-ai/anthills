"""
Claude Integration: ClaudeWorker for Anthropic's Claude API.

Provides a convenient base class for workers that use Claude to process
pheromones and generate responses.
"""

from __future__ import annotations

from typing import Any

from ..board import Pheromone
from ..worker import Worker, WorkerContext


class LLMWorker(Worker):
    """
    Base class for LLM-backed workers.
    
    Override build_messages() and optionally parse_response() to customize
    how pheromones are converted to LLM prompts and responses.
    """
    
    system_prompt: str = "You are a helpful AI agent."
    output_pheromone_type: str = "llm.response"
    model: str = ""
    
    async def build_messages(self, pheromone: Pheromone) -> list[dict]:
        """
        Build the messages list for the LLM call.
        
        Override this to customize prompt construction.
        
        Args:
            pheromone: The triggering pheromone
            
        Returns:
            List of message dicts for the LLM
        """
        return [{"role": "user", "content": str(pheromone.payload)}]
    
    async def parse_response(self, response: Any, pheromone: Pheromone) -> dict:
        """
        Parse the LLM response into a pheromone payload.
        
        Override this to customize response handling.
        
        Args:
            response: The raw LLM response
            pheromone: The triggering pheromone
            
        Returns:
            Dict to use as the output pheromone payload
        """
        return {"result": str(response), "source_pheromone_id": pheromone.id}
    
    async def call_llm(self, messages: list[dict]) -> Any:
        """
        Call the LLM with the given messages.
        
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement call_llm()")
    
    async def handle(self, ctx: WorkerContext) -> None:
        """
        Handle a pheromone by calling the LLM and depositing the response.
        """
        messages = await self.build_messages(ctx.pheromone)
        response = await self.call_llm(messages)
        output_payload = await self.parse_response(response, ctx.pheromone)
        
        ctx.deposit(
            type=self.output_pheromone_type,
            payload=output_payload,
        )


class ClaudeWorker(LLMWorker):
    """
    Worker that uses Anthropic's Claude API.
    
    Example:
        @colony.worker(reacts_to="task.created")
        class Researcher(ClaudeWorker):
            system_prompt = "You are a research assistant."
            output_pheromone_type = "research.complete"
            
            async def build_messages(self, pheromone):
                return [{"role": "user", "content": f"Research: {pheromone.payload['topic']}"}]
    """
    
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    tools: list[dict] = []
    
    _client = None
    
    @classmethod
    def _get_client(cls):
        """Get or create the Anthropic client."""
        if cls._client is None:
            try:
                from anthropic import AsyncAnthropic
                cls._client = AsyncAnthropic()
            except ImportError:
                raise ImportError(
                    "ClaudeWorker requires the anthropic package. "
                    "Install it with: pip install anthills[claude]"
                )
        return cls._client
    
    async def call_llm(self, messages: list[dict]) -> Any:
        """Call Claude API with the given messages."""
        client = self._get_client()
        
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
        }
        
        if self.tools:
            kwargs["tools"] = self.tools
        
        response = await client.messages.create(**kwargs)
        return response
    
    async def parse_response(self, response: Any, pheromone: Pheromone) -> dict:
        """
        Parse Claude's response into a pheromone payload.
        
        Handles both text and tool_use content blocks.
        """
        text_blocks = []
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        
        return {
            "result": "\n".join(text_blocks) if text_blocks else "",
            "tool_calls": tool_calls,
            "source_pheromone_id": pheromone.id,
            "model": self.model,
            "stop_reason": response.stop_reason,
        }


class ClaudeToolWorker(ClaudeWorker):
    """
    Claude worker with automatic tool execution loop.
    
    Continues calling Claude until it stops requesting tools.
    """
    
    tool_handlers: dict[str, callable] = {}
    max_tool_iterations: int = 10
    
    async def handle(self, ctx: WorkerContext) -> None:
        """Handle with tool execution loop."""
        messages = await self.build_messages(ctx.pheromone)
        
        for _ in range(self.max_tool_iterations):
            response = await self.call_llm(messages)
            
            # Check for tool calls
            tool_calls = [b for b in response.content if b.type == "tool_use"]
            
            if not tool_calls:
                # No more tools, we're done
                output_payload = await self.parse_response(response, ctx.pheromone)
                ctx.deposit(type=self.output_pheromone_type, payload=output_payload)
                return
            
            # Add assistant message
            messages.append({"role": "assistant", "content": response.content})
            
            # Execute tools and add results
            tool_results = []
            for tool_call in tool_calls:
                handler = self.tool_handlers.get(tool_call.name)
                if handler:
                    try:
                        result = await handler(**tool_call.input)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Unknown tool: {tool_call.name}"
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": str(result),
                })
            
            messages.append({"role": "user", "content": tool_results})
        
        # Max iterations reached
        ctx.deposit(
            type="worker.max_iterations",
            payload={
                "worker_id": self.id,
                "pheromone_id": ctx.pheromone.id,
                "iterations": self.max_tool_iterations,
            },
        )
