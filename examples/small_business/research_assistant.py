#!/usr/bin/env python3
"""
AI-Powered Research Assistant Demo

Uses Claude to research topics with multiple specialized workers.
This colony:
1. Takes a research topic
2. Plans the research approach
3. Researches sub-topics in parallel
4. Synthesizes findings into a report

This demonstrates:
- Integration with Claude API
- LLM-powered workers
- Fan-out/fan-in pattern (parallel research, then synthesis)
- Structured prompting

Requires: pip install anthills[claude]
Set: ANTHROPIC_API_KEY environment variable
"""

import asyncio
import os
from anthills import Colony, Pheromone

# Check for API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("⚠️  Warning: ANTHROPIC_API_KEY not set. Using mock responses.")
    USE_MOCK = True
else:
    USE_MOCK = False
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
    except ImportError:
        print("⚠️  anthropic package not installed. Using mock responses.")
        USE_MOCK = True


async def call_claude(system: str, prompt: str, max_tokens: int = 1024) -> str:
    """Call Claude API or return mock response."""
    if USE_MOCK:
        # Return mock responses for demo without API key
        return f"[Mock Claude response for: {prompt[:50]}...]"
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


async def main():
    colony = Colony(name="research-assistant", auto_halt=True, idle_timeout=2)
    
    # Track research progress
    research_results: dict[str, list] = {}
    
    # ==========================================================================
    # WORKER: Research Planner - Create research plan
    # ==========================================================================
    @colony.worker(reacts_to="research.requested")
    async def plan_research(ctx):
        """Create a research plan with sub-topics to investigate."""
        request = ctx.pheromone.payload
        topic = request.get("topic")
        depth = request.get("depth", "standard")
        
        print(f"📋 Planning research on: {topic}")
        
        system = """You are a research planning assistant. Given a topic, 
        identify 3-4 key sub-topics or questions to investigate.
        Return ONLY a JSON array of strings, nothing else.
        Example: ["subtopic 1", "subtopic 2", "subtopic 3"]"""
        
        prompt = f"Create a research plan for: {topic}\nDepth: {depth}"
        
        response = await call_claude(system, prompt)
        
        # Parse subtopics (in production, use proper JSON parsing)
        if USE_MOCK:
            subtopics = [
                f"History and background of {topic}",
                f"Current state and trends in {topic}",
                f"Future outlook for {topic}",
            ]
        else:
            import json
            try:
                subtopics = json.loads(response)
            except:
                subtopics = [topic]  # Fallback
        
        research_id = request.get("id", "research-001")
        research_results[research_id] = []
        
        print(f"📝 Research plan created with {len(subtopics)} subtopics")
        for i, st in enumerate(subtopics, 1):
            print(f"   {i}. {st}")
        
        await ctx.deposit(
            type="research.planned",
            payload={
                "research_id": research_id,
                "topic": topic,
                "subtopics": subtopics,
                "total_subtopics": len(subtopics),
            },
        )
        
        # Trigger research on each subtopic
        for subtopic in subtopics:
            await ctx.deposit(
                type="subtopic.research",
                payload={
                    "research_id": research_id,
                    "main_topic": topic,
                    "subtopic": subtopic,
                },
            )
    
    # ==========================================================================
    # WORKER: Subtopic Researcher - Research individual subtopics
    # ==========================================================================
    @colony.worker(reacts_to="subtopic.research")
    async def research_subtopic(ctx):
        """Research a specific subtopic."""
        data = ctx.pheromone.payload
        research_id = data.get("research_id")
        main_topic = data.get("main_topic")
        subtopic = data.get("subtopic")
        
        print(f"🔍 Researching: {subtopic}")
        
        system = """You are a research assistant. Provide a concise but informative 
        summary of the given subtopic in the context of the main topic.
        Focus on key facts, recent developments, and important considerations.
        Keep the response under 200 words."""
        
        prompt = f"Main topic: {main_topic}\nSubtopic to research: {subtopic}"
        
        findings = await call_claude(system, prompt)
        
        print(f"✅ Completed research on: {subtopic[:40]}...")
        
        await ctx.deposit(
            type="subtopic.complete",
            payload={
                "research_id": research_id,
                "subtopic": subtopic,
                "findings": findings,
            },
        )
    
    # ==========================================================================
    # WORKER: Research Aggregator - Collect all subtopic results
    # ==========================================================================
    @colony.worker(reacts_to="subtopic.complete")
    async def aggregate_research(ctx):
        """Collect subtopic research and trigger synthesis when complete."""
        data = ctx.pheromone.payload
        research_id = data.get("research_id")
        
        # Store this result
        if research_id not in research_results:
            research_results[research_id] = []
        research_results[research_id].append({
            "subtopic": data.get("subtopic"),
            "findings": data.get("findings"),
        })
        
        # Check if all subtopics are complete
        planned = ctx.board.read(type="research.planned")
        plan = next((p.payload for p in planned if p.payload.get("research_id") == research_id), None)
        
        if plan and len(research_results[research_id]) >= plan.get("total_subtopics", 0):
            print(f"\n📚 All {len(research_results[research_id])} subtopics researched")
            
            await ctx.deposit(
                type="research.ready_for_synthesis",
                payload={
                    "research_id": research_id,
                    "topic": plan.get("topic"),
                    "results": research_results[research_id],
                },
            )
    
    # ==========================================================================
    # WORKER: Synthesizer - Create final report
    # ==========================================================================
    @colony.worker(reacts_to="research.ready_for_synthesis")
    async def synthesize_report(ctx):
        """Synthesize all research into a final report."""
        data = ctx.pheromone.payload
        research_id = data.get("research_id")
        topic = data.get("topic")
        results = data.get("results", [])
        
        print(f"✍️  Synthesizing final report...")
        
        # Build context from all research
        research_context = "\n\n".join([
            f"## {r['subtopic']}\n{r['findings']}"
            for r in results
        ])
        
        system = """You are a research report writer. Given research on multiple subtopics,
        create a cohesive executive summary that:
        1. Introduces the topic
        2. Highlights key findings
        3. Draws connections between subtopics
        4. Provides actionable insights or conclusions
        
        Keep the report concise but comprehensive (300-400 words)."""
        
        prompt = f"Topic: {topic}\n\nResearch Findings:\n{research_context}"
        
        report = await call_claude(system, prompt, max_tokens=1500)
        
        print(f"\n📄 Report generated!")
        
        await ctx.deposit(
            type="research.complete",
            payload={
                "research_id": research_id,
                "topic": topic,
                "report": report,
                "sources_count": len(results),
            },
        )
        
        # Cleanup
        if research_id in research_results:
            del research_results[research_id]
    
    # ==========================================================================
    # WORKER: Report Publisher - Output the final report
    # ==========================================================================
    @colony.worker(reacts_to="research.complete")
    async def publish_report(ctx):
        """Output the final research report."""
        data = ctx.pheromone.payload
        
        print("\n" + "=" * 60)
        print(f"📊 RESEARCH REPORT: {data.get('topic')}")
        print("=" * 60)
        print(data.get("report"))
        print("=" * 60)
        print(f"Sources synthesized: {data.get('sources_count')}")
    
    # ==========================================================================
    # Run the research assistant
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🔬 AI RESEARCH ASSISTANT DEMO")
    print("=" * 60 + "\n")
    
    # Trigger a research request
    colony.deposit(
        type="research.requested",
        payload={
            "id": "research-001",
            "topic": "The impact of AI on small business operations",
            "depth": "standard",
            "requested_by": "demo_user",
        },
    )
    
    # Run the colony
    await colony.run_async()


if __name__ == "__main__":
    asyncio.run(main())
