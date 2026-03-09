"""
Example: Multi-agent research pipeline using stigmergy.

Workers react to pheromones and deposit new ones,
creating an emergent research workflow.

No explicit messaging. No central coordinator.
Just signals in the environment.
"""

from anthills import Colony, Pheromone


def main():
    # Create a colony (shared environment + workers)
    colony = Colony(
        name="research-pipeline",
        auto_halt=True,
        idle_timeout=3,
    )
    
    # Track results for demo output
    results = {"researched": [], "summarized": []}
    
    # Worker 1: Researcher
    # Reacts to "topic.queued" and deposits "research.complete"
    @colony.worker(reacts_to="topic.queued")
    async def researcher(pheromone, board):
        topic = pheromone.payload["topic"]
        print(f"🔬 Researcher: Starting research on '{topic}'")
        
        # Simulate research (in real app, call LLM or search API)
        findings = [
            f"Finding 1: {topic} is an emerging field",
            f"Finding 2: Key players include several tech companies",
            f"Finding 3: Recent advances show promising results",
        ]
        
        results["researched"].append(topic)
        
        # Deposit findings for other workers
        board.deposit(Pheromone(
            type="research.complete",
            payload={
                "topic": topic,
                "findings": findings,
            },
            deposited_by="researcher",
            trail_id=pheromone.trail_id,
        ))
        print(f"🔬 Researcher: Deposited findings for '{topic}'")
    
    # Worker 2: Synthesizer
    # Reacts to "research.complete" and deposits "summary.ready"
    @colony.worker(reacts_to="research.complete")
    async def synthesizer(pheromone, board):
        topic = pheromone.payload["topic"]
        findings = pheromone.payload["findings"]
        print(f"📝 Synthesizer: Synthesizing findings for '{topic}'")
        
        # Simulate synthesis
        summary = f"Summary of {topic}: " + " | ".join(findings)
        
        results["summarized"].append(summary)
        
        board.deposit(Pheromone(
            type="summary.ready",
            payload={"topic": topic, "summary": summary},
            deposited_by="synthesizer",
            trail_id=pheromone.trail_id,
        ))
        print(f"📝 Synthesizer: Summary ready for '{topic}'")
    
    # Worker 3: Reporter (optional - just logs completions)
    @colony.worker(reacts_to="summary.ready")
    async def reporter(pheromone, board):
        topic = pheromone.payload["topic"]
        print(f"✅ Reporter: Pipeline complete for '{topic}'")
    
    # =========================================
    # Run the pipeline
    # =========================================
    print("=" * 60)
    print("🐜 ANTHILLS: Stigmergic Research Pipeline")
    print("=" * 60)
    print("\nDepositing initial topics...\n")
    
    # Deposit initial tasks - workers will chain from here
    colony.deposit(type="topic.queued", payload={"topic": "AI Agent Frameworks"})
    colony.deposit(type="topic.queued", payload={"topic": "Stigmergy in Nature"})
    
    # Run the colony - it will auto-halt when idle
    colony.run()
    
    # =========================================
    # Show results
    # =========================================
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    print(f"\nTopics researched: {len(results['researched'])}")
    for topic in results["researched"]:
        print(f"  - {topic}")
    
    print(f"\nSummaries generated: {len(results['summarized'])}")
    for summary in results["summarized"]:
        print(f"  - {summary[:80]}...")
    
    # Show ledger (audit trail)
    print(f"\n📜 Event Ledger: {len(colony.events())} events recorded")
    for event in colony.events()[:5]:
        print(f"  [{event.event_type}] {event.pheromone.type if event.pheromone else 'N/A'}")
    if len(colony.events()) > 5:
        print(f"  ... and {len(colony.events()) - 5} more")


if __name__ == "__main__":
    main()
