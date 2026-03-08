"""
LLM Integration: Claude via Anthropic API.
"""

import json
import os
from typing import Any, Dict, List, Optional
from anthropic import Anthropic


class ClaudeAgent:
    """Wrapper around Claude for agent decision-making."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = Anthropic(api_key=self.api_key)
    
    def think(
        self,
        name: str,
        goal: str,
        pheromones: Dict[str, Any],
        available_tools: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Ask Claude what action to take given:
        - The agent's goal
        - Current pheromones (environmental state)
        - Available tools
        
        Returns:
            {
                "thought": "what the agent is thinking",
                "action": "tool_name",
                "input": {...},
                "reasoning": "why this action"
            }
        """
        if conversation_history is None:
            conversation_history = []
        
        system_prompt = f"""You are an agent named "{name}" in a multi-agent swarm.

Your goal: {goal}

You can perceive pheromones (traces left by other agents in the shared environment).
You can act by calling tools.
You leave traces for other agents to sense.

Think carefully about:
1. What traces are saying (other agents' work)
2. What needs to be done to reach your goal
3. Which tool to use next

Available tools: {', '.join(available_tools)}

Respond ONLY with valid JSON (no markdown, no extra text):
{{
    "thought": "what you're thinking",
    "action": "tool_name_to_call",
    "input": {{"param": "value"}},
    "reasoning": "why this action"
}}"""
        
        pheromone_str = json.dumps(pheromones, indent=2)
        
        user_message = f"""Current pheromones (environmental state):
{pheromone_str}

What should you do next? Respond with JSON only."""
        
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=system_prompt,
            messages=conversation_history
        )
        
        response_text = response.content[0].text.strip()
        
        # Try to parse as JSON
        try:
            decision = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if Claude doesn't return valid JSON
            decision = {
                "thought": response_text,
                "action": "wait",
                "input": {},
                "reasoning": "Could not parse response"
            }
        
        conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        
        return decision
