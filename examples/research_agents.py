"""
Example: Two agents researching a topic together.

Researcher Agent:
- Reads the topic
- Searches for information
- Deposits findings

Synthesizer Agent:
- Senses researcher's deposits
- Synthesizes findings
- Deposits summary

No explicit messaging between them. Just pheromones.
"""

import sys
sys.path.insert(0, '..')

from anthills import Agent, PheromoneBoard


def main():
    # Shared environment
    board = PheromoneBoard(default_ttl_hours=2)
    
    # Agent 1: Researcher
    researcher = Agent(
        name="researcher",
        goal="Research the topic 'AI agent frameworks' and find key information",
        pheromone_board=board,
        tools=["web_search", "wait"],
        max_iterations=3
    )
    
    # Agent 2: Synthesizer
    synthesizer = Agent(
        name="synthesizer",
        goal="Synthesize the research findings into a coherent summary",
        pheromone_board=board,
        tools=["synthesize", "wait"],
        max_iterations=3
    )
    
    print("=" * 60)
    print("STIGMERGY: Two Agents Research Together (No Explicit Messaging)")
    print("=" * 60)
    print("\n🐜 Researcher Agent starting...\n")
    
    # Run researcher for a few steps
    for i in range(2):
        researcher.step()
    
    print("\n🐜 Synthesizer Agent starting (sensing researcher's work)...\n")
    
    # Run synthesizer - it will sense researcher's traces
    for i in range(2):
        synthesizer.step()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    print("\n📊 Researcher Summary:")
    for key, val in researcher.summary().items():
        print(f"  {key}: {val}")
    
    print("\n📊 Synthesizer Summary:")
    for key, val in synthesizer.summary().items():
        print(f"  {key}: {val}")
    
    print("\n🧪 Pheromone Board State:")
    summary = board.summary()
    print(f"  Trace types: {summary['trace_types']}")
    print(f"  Total active traces: {summary['total_traces']}")
    print(f"  Strengths: {summary['strengths']}")
    
    print("\n✅ Example complete!")
    print("Notice: Agents coordinated without explicit messaging.")
    print("Each agent sensed the other's pheromones and responded.")


if __name__ == "__main__":
    main()
