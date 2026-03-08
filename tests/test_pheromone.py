"""
Basic tests for PheromoneBoard.
"""

import sys
sys.path.insert(0, '..')

from stigmergy import PheromoneBoard


def test_deposit_and_read():
    """Test depositing and reading pheromones."""
    board = PheromoneBoard()
    
    # Deposit a trace
    board.deposit(
        trace_type="research",
        content={"finding": "LLMs are good at reasoning"},
        source="agent_a"
    )
    
    # Read it back
    traces = board.read("research")
    assert len(traces) == 1
    assert traces[0]["content"]["finding"] == "LLMs are good at reasoning"
    assert traces[0]["source"] == "agent_a"
    
    print("✅ test_deposit_and_read passed")


def test_strength():
    """Test pheromone strength calculation."""
    board = PheromoneBoard()
    
    # Fresh traces have high strength
    board.deposit("research", {"data": "test"}, source="agent_a")
    strength = board.strength("research")
    assert strength > 0.9  # Very fresh
    
    # Non-existent type has zero strength
    assert board.strength("nonexistent") == 0.0
    
    print("✅ test_strength passed")


def test_by_source():
    """Test reading traces by source."""
    board = PheromoneBoard()
    
    board.deposit("task", {"work": "1"}, source="agent_a")
    board.deposit("task", {"work": "2"}, source="agent_b")
    board.deposit("debug", {"error": "1"}, source="agent_a")
    
    agent_a_traces = board.read_by_source("agent_a")
    assert len(agent_a_traces) == 2  # Both "task" and "debug"
    
    agent_a_tasks = board.read_by_source("agent_a", trace_type="task")
    assert len(agent_a_tasks) == 1  # Only "task"
    
    print("✅ test_by_source passed")


def test_summary():
    """Test board summary."""
    board = PheromoneBoard()
    
    board.deposit("research", {"data": "1"}, source="agent_a")
    board.deposit("debug", {"error": "1"}, source="agent_b")
    
    summary = board.summary()
    assert "research" in summary["trace_types"]
    assert "debug" in summary["trace_types"]
    assert summary["total_traces"] == 2
    
    print("✅ test_summary passed")


if __name__ == "__main__":
    test_deposit_and_read()
    test_strength()
    test_by_source()
    test_summary()
    print("\n✅ All tests passed!")
