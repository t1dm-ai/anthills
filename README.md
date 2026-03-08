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

## Install

**Via PyPI (recommended):**

```bash
pip install anthills
```

**From source:**

```bash
git clone https://github.com/dbrasuell/anthills
cd anthills
pip install -e .
```

## Quick Start

```bash
export ANTHROPIC_API_KEY="sk-..."
python -m examples.research_agents
```

Or run the T1D simulation:

```bash
python -m examples.t1d_simulation
```

## How It Works

### The Pheromone Board

Shared memory where agents leave traces:

```python
from anthills import PheromoneBoard

board = PheromoneBoard()
board.deposit("research", {
    "topic": "LLM reasoning",
    "findings": ["extended thinking works", "costs are high"],
    "source": "agent_research"
})
```

### Agent Loop

```python
from anthills import Agent

agent = Agent(name="researcher", goal="Research X", pheromone_board=board)
while not agent.completed:
    agent.step()  # perceive → think → act → deposit
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
- **`t1d_simulation.py`** — Type 1 Diabetes pathophysiology model
- **`debug_agents.py`** — Three agents debugging code collaboratively
- **`build_agents.py`** — Agents building a feature end-to-end

See `examples/` directory and `examples/T1D_README.md` for details.

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
python -m examples.t1d_simulation
```

This runs two scenarios:
- **High-risk**: Genetic predisposition + viral trigger → Fast T1D onset
- **Low-risk**: Genetic resistance, no trigger → Slower/no progression

The output shows day-by-day progression of glucose, insulin, inflammation, and beta cell count.

See `examples/T1D_README.md` for full details.

## Project Structure

```
anthills/
├── README.md
├── pyproject.toml
├── anthills/
│   ├── __init__.py
│   ├── agent.py              # Base Agent class
│   ├── pheromone.py          # Shared environment
│   ├── tools.py              # Tool definitions
│   ├── llm.py                # Claude integration
│   └── environments/
│       ├── __init__.py
│       └── t1d.py            # T1D simulation
├── examples/
│   ├── research_agents.py
│   ├── t1d_simulation.py
│   ├── debug_agents.py
│   └── T1D_README.md
└── tests/
    └── test_pheromone.py
```

## Philosophy

This is **not** a general-purpose agent framework. It's a specific take: **agents coordinating through environmental traces, not explicit messaging.**

Use it when you want:
- Multiple agents collaborating on complex tasks
- Self-organization without central orchestration
- Transparent, auditable agent behavior
- Resilience to individual agent failures

## Roadmap

- [ ] Real-time dashboard (visualize pheromone board)
- [ ] Agent profiler (performance metrics)
- [ ] Trace debugger (replay decisions step-by-step)
- [ ] More environments (stock market, code debugging, research)
- [ ] Parallel agent execution
- [ ] Browser automation tools
- [ ] Database access tools
- [ ] Webhooks / external event triggers

## Building This in Public

This project is being built on Twitter: [@braz_builds](https://twitter.com/braz_builds)

Daily updates on architecture, insights, and use cases.

---

**Built with Claude + Python. Inspired by ant colonies. 🐜**

[Read the full documentation](./examples/T1D_README.md) | [View on PyPI](https://pypi.org/project/anthills/)
