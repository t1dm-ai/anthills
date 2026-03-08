"""
Agent: Autonomous unit in the swarm.

Agents:
1. Perceive pheromones (environmental state)
2. Think (using Claude)
3. Act (call tools)
4. Deposit pheromones (leave traces for others)
"""

from typing import Any, Dict, List, Optional
from .pheromone import PheromoneBoard
from .llm import ClaudeAgent
from .tools import ToolRegistry


class Agent:
    """
    Autonomous agent that coordinates with others through pheromones.
    """
    
    def __init__(
        self,
        name: str,
        goal: str,
        pheromone_board: PheromoneBoard,
        tools: Optional[List[str]] = None,
        max_iterations: int = 10
    ):
        """
        Initialize an agent.
        
        Args:
            name: Agent identifier
            goal: What this agent is trying to accomplish
            pheromone_board: Shared environment (reference to same board)
            tools: List of tool names agent can use
            max_iterations: Max steps before stopping
        """
        self.name = name
        self.goal = goal
        self.pheromone_board = pheromone_board
        self.max_iterations = max_iterations
        
        self.llm = ClaudeAgent()
        self.tool_registry = ToolRegistry()
        self.tools = tools or self.tool_registry.list_tools()
        
        self.conversation_history: List[Dict[str, str]] = []
        self.iteration = 0
        self.completed = False
        self.actions_taken: List[Dict[str, Any]] = []
    
    def perceive(self) -> Dict[str, Any]:
        """
        Read pheromones from the board.
        
        Returns environmental state (what other agents have done/found).
        """
        # Evict expired traces
        self.pheromone_board.evict_expired()
        
        # Read all active pheromones
        pheromones = {}
        for trace_type in self.pheromone_board.traces.keys():
            traces = self.pheromone_board.read(trace_type, limit=5)
            pheromones[trace_type] = [t["content"] for t in traces]
        
        # Also include strength (concentration) of pheromones
        strengths = {t: self.pheromone_board.strength(t) for t in self.pheromone_board.traces.keys()}
        
        return {
            "pheromones": pheromones,
            "strengths": strengths,
            "my_previous_work": [t["content"] for t in self.pheromone_board.read_by_source(self.name)]
        }
    
    def think(self, environmental_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Claude to decide what to do next.
        
        Returns decision (thought, action, input, reasoning).
        """
        decision = self.llm.think(
            name=self.name,
            goal=self.goal,
            pheromones=environmental_state,
            available_tools=self.tools,
            conversation_history=self.conversation_history
        )
        
        return decision
    
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action (call a tool).
        
        Returns result of the tool call.
        """
        action = decision.get("action", "wait")
        inputs = decision.get("input", {})
        
        result = self.tool_registry.call(action, **inputs)
        
        return {
            "action": action,
            "inputs": inputs,
            "result": result
        }
    
    def deposit(self, trace_type: str, content: Any, ttl_hours: int = 1) -> None:
        """
        Leave a pheromone trace for other agents.
        """
        self.pheromone_board.deposit(
            trace_type=trace_type,
            content=content,
            source=self.name,
            ttl_hours=ttl_hours
        )
    
    def step(self) -> Dict[str, Any]:
        """
        Execute one full cycle: perceive → think → act → deposit.
        
        Returns summary of what happened.
        """
        self.iteration += 1
        
        # 1. PERCEIVE
        env_state = self.perceive()
        
        # 2. THINK
        decision = self.think(env_state)
        
        # 3. ACT
        action_result = self.act(decision)
        
        # 4. DEPOSIT
        self.deposit(
            trace_type="agent_activity",
            content={
                "agent": self.name,
                "iteration": self.iteration,
                "action": decision.get("action"),
                "result": action_result["result"].get("result") if action_result["result"].get("success") else "failed"
            }
        )
        
        # Store for later review
        self.actions_taken.append({
            "iteration": self.iteration,
            "decision": decision,
            "result": action_result
        })
        
        return {
            "agent": self.name,
            "iteration": self.iteration,
            "decision": decision,
            "result": action_result
        }
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Run the agent until it completes or hits max iterations.
        
        Returns history of all steps taken.
        """
        while self.iteration < self.max_iterations and not self.completed:
            step_result = self.step()
            print(f"\n[{self.name}] Iteration {self.iteration}")
            print(f"  Action: {step_result['decision'].get('action')}")
            print(f"  Result: {step_result['result']}")
            
            # Check if action was "done"
            if step_result["decision"].get("action") == "done":
                self.completed = True
                self.deposit(
                    trace_type="completion",
                    content={
                        "agent": self.name,
                        "completed_at": self.iteration,
                        "goal": self.goal
                    }
                )
                break
        
        return self.actions_taken
    
    def summary(self) -> Dict[str, Any]:
        """Get a summary of what this agent did."""
        return {
            "name": self.name,
            "goal": self.goal,
            "iterations": self.iteration,
            "completed": self.completed,
            "actions": len(self.actions_taken),
            "actions_taken": [
                {
                    "iteration": a["iteration"],
                    "action": a["decision"].get("action"),
                    "success": a["result"]["result"].get("success")
                }
                for a in self.actions_taken
            ]
        }
