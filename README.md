# Anthills 🐜

**Multi-agent coordination without explicit messaging.**

Inspired by ant colonies, where simple agents leave chemical trails (pheromones) that other agents sense and respond to — creating emergent swarm intelligence.

## The Idea

Most multi-agent frameworks require explicit coordination: Agent A tells Agent B what to do. Message passing. Explicit protocols.

**Anthills does the opposite.** Agents:
1. **Perceive** the shared environment (pheromone board)
2. **Think** independently using Claude
3. **Act** on the environment (call tools)
4. **Leave traces** for other agents to sense

No explicit messaging. No central coordinator. Just local behavior creating emergent coordination.

```
Agent A finds research → leaves trace
Agent B senses trace → builds on it
Agent C senses both → generates code
All coordinating like an ant colony.
```

## Why This Matters

- **Scalable:** Add more agents, they self-organize
- **Resilient:** Agents fail independently, others adapt
- **Simple:** Each agent is dumb; intelligence emerges
- **Transparent:** You can see what agents are sensing/doing

## Quick Start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-..."
python examples/research_agents.py
```

## How It Works

### The Pheromone Board
Shared memory where agents leave traces:
```python
pheromone.deposit("research", {
    "topic": "LLM reasoning",
    "findings": ["extended thinking works", "costs are high"],
    "source": "agent_research"
})
```

### Agent Loop
```python
agent = Agent(name="researcher", tools=[web_search, read_file])
while not done:
    traces = pheromone.read("research")  # Perceive
    next_action = agent.think(traces)     # Think
    result = agent.act(next_action)       # Act
    pheromone.deposit("research", result) # Leave trace
```

### Example: Two Agents, No Explicit Messaging

**Agent A (Researcher):**
- Reads pheromone board
- Thinks: "I should research X"
- Acts: calls web_search
- Deposits: "Found 3 papers"

**Agent B (Synthesizer):**
- Reads pheromone board
- Senses A's deposit: "3 papers found"
- Thinks: "I should synthesize these"
- Acts: calls code_exec to process
- Deposits: "Synthesis complete"

No message passing. No protocol. Just traces in the environment.

## Examples

- **`research_agents.py`** — Two agents researching a topic together
- **`t1d_simulation.py`** — Type 1 Diabetes pathophysiology model (see below)
- **`debug_agents.py`** — Three agents debugging code collaboratively
- **`build_agents.py`** — Agents building a feature end-to-end

## Real-World Application: Type 1 Diabetes Simulation

**[NEW]** Anthills models the multi-agent dynamics of Type 1 Diabetes.

### The Biology

T1D emerges from anthills-like coordination failure:

```
BetaCells ↔ ImmuneSystem (no direct messaging)
     ↓ (sense pheromones)
  Glucose, Insulin, Cytokines, Antigens
     ↑
  Local responses → Emergent autoimmunity
```

1. **Genetic predisposition** — HLA genes increase autoimmune risk
2. **Environmental trigger** — Viral infection breaks tolerance
3. **Beta cell autoimmunity** — Immune attacks insulin-producing cells (no central controller)
4. **Positive feedback** — Cell death → more inflammation → more attack
5. **Clinical T1D** — ~80% beta cell loss → insulin-dependent diabetes

### Run the Simulation

```bash
python examples/t1d_simulation.py
```

This runs two scenarios:
- **High-risk**: Genetic predisposition + viral trigger → Fast T1D onset
- **Low-risk**: Genetic resistance, no trigger → Slower/no progression

The output shows day-by-day progression of glucose, insulin, inflammation, and beta cell count.

## Project Structure

```
anthills/
├── README.md
├── requirements.txt
├── anthills/
│   ├── __init__.py
│   ├── agent.py           # Base Agent class
│   ├── pheromone.py       # Shared environment
│   ├── tools.py           # Tool definitions
│   └── llm.py             # Claude integration
├── examples/
│   ├── research_agents.py
│   ├── debug_agents.py
│   └── build_agents.py
└── tests/
    └── test_agent.py
```

## Philosophy

This is **not** a general-purpose agent framework. It's a specific take: **agents coordinating through environmental traces, not explicit messaging.**

Use it when you want:
- Multiple agents collaborating on complex tasks
- Self-organization without central orchestration
- Transparent, auditable agent behavior
- Resilience to individual agent failures

## Roadmap

- [ ] Multi-pheromone types (strength, TTL, priority)
- [ ] Agent memory (persistent traces)
- [ ] Visualization (see the pheromone board in real-time)
- [ ] Streaming agent responses
- [ ] More tools (code execution, file I/O, external APIs)

## Building This in Public

This project is being built on Twitter: [@braz_builds](https://twitter.com/braz_builds)

Daily updates on architecture, insights, and use cases.

---

**Built with Claude + Python + Anthills vibes 🐜**
