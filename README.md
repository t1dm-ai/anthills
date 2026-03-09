# Anthills 🐜

> **Stigmergy-based AI agent orchestration.** Agents coordinate through a shared environment — not a central planner.

[![PyPI version](https://badge.fury.io/py/anthills.svg)](https://pypi.org/project/anthills/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is Anthills?

Most agent frameworks orchestrate through a central controller — a graph, a DAG, a router that decides who does what next.

**Anthills is different.** It borrows from nature.

In an ant colony, no single ant knows the plan. Instead, ants deposit *pheromones* — signals in the environment — and other ants respond to those signals. Complex, adaptive behavior emerges from simple local rules. No orchestrator required.

Anthills brings this model to AI agents:

- Agents read from and write to a shared **Pheromone Board** — a persistent, observable environment
- Coordination is **emergent**, not prescribed
- Any agent can react to any signal — enabling flexible, parallel, self-organizing workflows
- The full history of signals is captured as a **ledger** — making agent behavior auditable and replayable

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Pheromone Board** | The shared environment all agents read from and write to |
| **Pheromone** | A signal deposited by an agent — carries type, intensity, payload, and TTL |
| **Worker** | An agent that reacts to pheromones and may deposit new ones |
| **Trail** | A sequence of pheromone deposits that form an emergent task path |
| **Colony** | A named group of workers sharing a pheromone board |
| **Ledger** | Append-only log of all pheromone events — the source of truth for tracing |

---

## Installation

```bash
pip install anthills
```

For Claude integration:
```bash
pip install anthills[claude]
```

---

## Quick Start

```python
from anthills import Colony, Pheromone

# Define a colony (shared environment)
colony = Colony(name="research-pipeline")

# Define workers that react to signals
@colony.worker(reacts_to="task.created")
async def researcher(pheromone, board):
    # Process the pheromone
    result = f"Researched: {pheromone.payload['topic']}"
    # Deposit a new signal for other workers
    board.deposit(Pheromone(
        type="research.complete",
        payload={"findings": result},
        deposited_by="researcher",
    ))

@colony.worker(reacts_to="research.complete")
async def summarizer(pheromone, board):
    summary = f"Summary of: {pheromone.payload['findings']}"
    board.deposit(Pheromone(
        type="summary.ready",
        payload={"summary": summary},
        deposited_by="summarizer",
    ))

# Kick off the colony with an initial signal
colony.deposit(type="task.created", payload={"topic": "quantum computing"})
colony.run()
```

No graph definition. No router. Workers emerge into action as signals appear.

---

## With Claude (LLM Integration)

```python
from anthills import Colony
from anthills.integrations.claude import ClaudeWorker

colony = Colony(name="research")

@colony.worker(reacts_to="topic.queued")
class Researcher(ClaudeWorker):
    system_prompt = "You are a research assistant."
    output_pheromone_type = "research.complete"

    async def build_messages(self, pheromone):
        return [{"role": "user", "content": f"Summarize: {pheromone.payload['topic']}"}]

colony.deposit(type="topic.queued", payload={"topic": "stigmergy"})
colony.run()
```

---

## Why Stigmergy?

Traditional agent orchestration is **choreography** — someone writes the script.

Stigmergy is **emergence** — the environment carries the coordination logic.

This makes Anthills particularly well-suited for:

- **Long-running, async workflows** where tasks arrive unpredictably
- **Parallel multi-agent pipelines** where bottlenecks are hard to predict upfront
- **Adaptive systems** that need to self-organize around failures or new inputs
- **Observable AI workflows** where you need to understand *why* agents did what they did

---

## Examples

See the `examples/` directory:

- **`research_agents.py`** — Multi-agent research pipeline
- **`t1d_simulation.py`** — Type 1 Diabetes pathophysiology model (stigmergy in biology!)

---

## Development

```bash
git clone https://github.com/t1dm-ai/anthills
cd anthills
pip install -e ".[dev,claude]"
pytest
```

---

## Connectors

Connectors provide external tool integrations for your workers:

```python
from anthills import Colony
from anthills.connectors import ConnectorRegistry, requires
from anthills.connectors.gmail import GmailConnector
from anthills.connectors.slack import SlackConnector

# Create registry with configured connectors
registry = ConnectorRegistry()
registry.register(GmailConnector(credentials_path="/path/to/creds.json"))
registry.register(SlackConnector(bot_token="xoxb-..."))

# Create colony with connectors
colony = Colony(name="notifications", connectors=registry)

# Workers declare their connector requirements
@colony.worker(reacts_to="alert.triggered", requires=["gmail", "slack"])
async def notify(ctx):
    gmail = ctx.connectors["gmail"]
    slack = ctx.connectors["slack"]
    
    await gmail.send_email(to="team@example.com", subject="Alert", body="...")
    await slack.send_message(channel="#alerts", text="...")
```

### Built-in Connectors

| Connector | Install | Description |
|-----------|---------|-------------|
| `GmailConnector` | `pip install anthills[gmail]` | Send emails via Gmail API |
| `SlackConnector` | `pip install anthills[slack]` | Post messages to Slack |

### Custom Connectors

```python
from anthills.connectors import Connector, ConnectorConfig

class MyConnector(Connector):
    name = "my_service"
    
    async def connect(self) -> None:
        # Initialize connection
        pass
    
    async def disconnect(self) -> None:
        # Cleanup
        pass
```

---

## Colony Templates

Templates provide declarative, reusable colony configurations:

```python
from anthills.templates import TemplateCatalog, TemplateInstantiator

# Discover built-in templates
catalog = TemplateCatalog()
catalog.register_builtins()

# List available templates
for template in catalog.list():
    print(f"{template.name}: {template.description}")

# Instantiate a template with parameters
instantiator = TemplateInstantiator(catalog)
colony = instantiator.instantiate(
    "research_assistant",
    parameters={
        "research_depth": "comprehensive",
        "output_format": "markdown"
    }
)

colony.run()
```

### Built-in Templates

| Template | Description |
|----------|-------------|
| `customer_inquiry_responder` | Auto-respond to customer questions |
| `weekly_sales_summary` | Aggregate and report weekly sales data |
| `research_assistant` | Multi-step research with Claude |

### Custom Templates

```python
from anthills.templates import ColonyTemplate, WorkerSpec, TriggerSpec

template = ColonyTemplate(
    name="my_pipeline",
    description="Custom processing pipeline",
    workers=[
        WorkerSpec(
            name="processor",
            reacts_to="input.received",
            handler="my_module:process_handler",
            emits=["output.ready"]
        )
    ],
    triggers=[
        TriggerSpec(type="input.received", payload={"source": "api"})
    ]
)
```

---

## Project Structure

```
anthills/
├── board.py              # Event-sourced PheromoneBoard with wildcard patterns
├── worker.py             # Worker base class with retry & concurrency control
├── colony.py             # Colony runner (async event loop, auto-halt)
├── connectors/           # External tool integrations
│   ├── base.py           # Connector, ConnectorConfig, ConnectorRegistry
│   ├── registry.py       # Registry and requires() helper
│   ├── gmail/            # Gmail connector (optional)
│   └── slack/            # Slack connector (optional)
├── templates/            # Declarative colony configurations
│   ├── base.py           # ColonyTemplate, WorkerSpec, TriggerSpec
│   ├── catalog.py        # TemplateCatalog for discovery
│   ├── instantiator.py   # Convert templates to runnable colonies
│   └── builtins.py       # Built-in template definitions
└── integrations/
    └── claude.py         # ClaudeWorker, LLMWorker, ClaudeToolWorker
```

---

## Philosophy

This is **not** a general-purpose agent framework. It's a specific take: **agents coordinating through environmental traces, not explicit messaging.**

Use it when you want:
- Multiple agents collaborating on complex tasks
- Self-organization without central orchestration
- Transparent, auditable agent behavior
- Resilience to individual agent failures

## Roadmap

- [x] Event-sourced pheromone board with ledger
- [x] Wildcard pattern matching for pheromone types
- [x] Parallel agent execution with concurrency control
- [x] Connector abstraction for external tools
- [x] Colony templates for reusable configurations
- [x] Claude/LLM integration
- [ ] Real-time dashboard (visualize pheromone board)
- [ ] Agent profiler (performance metrics)
- [ ] Trace debugger (replay decisions step-by-step)
- [ ] Redis-backed board for distributed colonies
- [ ] More connectors (GitHub, Jira, databases)
- [ ] Webhooks / external event triggers

## Building This in Public

This project is being built on Twitter: [@braz_builds](https://twitter.com/braz_builds)

Daily updates on architecture, insights, and use cases.

---

**Built with Claude + Python. Inspired by ant colonies. 🐜**

[Read the full documentation](./examples/T1D_README.md) | [View on PyPI](https://pypi.org/project/anthills/)
