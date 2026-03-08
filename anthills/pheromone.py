"""
Pheromone Board: Shared environment for agent coordination.

Agents deposit traces; other agents sense them.
No explicit messaging - just environmental traces.
"""

import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class PheromoneBoard:
    """
    Shared memory where agents leave traces.
    
    Each trace has:
    - type: category of trace (e.g., "research", "debug", "build")
    - content: the actual data
    - source: which agent deposited it
    - timestamp: when it was deposited
    - ttl: how long it lives (default: 1 hour)
    """
    
    def __init__(self, default_ttl_hours: int = 1):
        self.traces: Dict[str, List[Dict[str, Any]]] = {}
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.history: List[Dict[str, Any]] = []
    
    def deposit(self, trace_type: str, content: Any, source: str = "unknown", ttl_hours: Optional[int] = None) -> None:
        """
        Deposit a pheromone trace into the board.
        
        Args:
            trace_type: Category of trace (e.g., "research", "debug")
            content: The actual data/information
            source: Which agent deposited this
            ttl_hours: How long the trace persists (default: 1 hour)
        """
        if trace_type not in self.traces:
            self.traces[trace_type] = []
        
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        expires_at = datetime.now() + ttl
        
        trace = {
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "id": f"{trace_type}_{len(self.traces[trace_type])}_{int(time.time())}"
        }
        
        self.traces[trace_type].append(trace)
        self.history.append(trace)
    
    def read(self, trace_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read traces of a specific type.
        
        Args:
            trace_type: Type of trace to read
            limit: Max number of traces to return (most recent first)
        
        Returns:
            List of non-expired traces, most recent first
        """
        if trace_type not in self.traces:
            return []
        
        now = datetime.now()
        active_traces = []
        
        for trace in self.traces[trace_type]:
            expires_at = datetime.fromisoformat(trace["expires_at"])
            if expires_at > now:
                active_traces.append(trace)
        
        # Sort by timestamp descending (most recent first)
        active_traces.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            return active_traces[:limit]
        return active_traces
    
    def read_by_source(self, source: str, trace_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Read traces deposited by a specific agent.
        
        Args:
            source: Agent name
            trace_type: Optional filter by type
        
        Returns:
            List of traces from that source
        """
        now = datetime.now()
        results = []
        
        types_to_check = [trace_type] if trace_type else self.traces.keys()
        
        for t in types_to_check:
            if t not in self.traces:
                continue
            
            for trace in self.traces[t]:
                if trace["source"] != source:
                    continue
                
                expires_at = datetime.fromisoformat(trace["expires_at"])
                if expires_at > now:
                    results.append(trace)
        
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    
    def evict_expired(self) -> int:
        """
        Remove expired traces from the board.
        
        Returns:
            Number of traces evicted
        """
        now = datetime.now()
        evicted = 0
        
        for trace_type in self.traces:
            original_count = len(self.traces[trace_type])
            self.traces[trace_type] = [
                t for t in self.traces[trace_type]
                if datetime.fromisoformat(t["expires_at"]) > now
            ]
            evicted += original_count - len(self.traces[trace_type])
        
        return evicted
    
    def strength(self, trace_type: str) -> float:
        """
        Calculate the "strength" of pheromones in a type.
        
        Higher = more recent activity in that area.
        
        Returns:
            0-1 score of pheromone concentration
        """
        traces = self.read(trace_type)
        if not traces:
            return 0.0
        
        now = datetime.now()
        weights = []
        
        for trace in traces:
            timestamp = datetime.fromisoformat(trace["timestamp"])
            age_seconds = (now - timestamp).total_seconds()
            # Decay over time (exponential)
            weight = max(0, 1 - (age_seconds / 3600))  # Decay over 1 hour
            weights.append(weight)
        
        return sum(weights) / len(weights) if weights else 0.0
    
    def summary(self) -> Dict[str, Any]:
        """Get a summary of the current board state."""
        return {
            "trace_types": list(self.traces.keys()),
            "total_traces": sum(len(self.read(t)) for t in self.traces.keys()),
            "strengths": {t: self.strength(t) for t in self.traces.keys()},
            "history_length": len(self.history)
        }
