# Small Business Examples

Real-world demos showing how small businesses can use Anthills for automation.

## Examples

### 1. Customer Support Triage (`support_triage.py`)
Auto-categorize and prioritize incoming support tickets.

**Workers:**
- **Categorizer** - Classifies tickets (billing, technical, account, general)
- **Priority Scorer** - Assigns urgency based on keywords and VIP status
- **Urgent Router** - Escalates urgent tickets to on-call team
- **Response Drafter** - Generates initial response templates
- **Metrics Collector** - Tracks all ticket events for analytics

**Run:** `python examples/small_business/support_triage.py`

---

### 2. Lead Qualification Pipeline (`lead_qualification.py`)
Score and route B2B leads based on company fit.

**Workers:**
- **Lead Enricher** - Fetches company data (simulated Clearbit/Apollo)
- **Lead Scorer** - Calculates fit score based on criteria
- **Hot Lead Router** - Notifies sales team of hot leads
- **Warm Lead Nurture** - Queues warm leads for email campaigns
- **Cold Lead Archive** - Stores cold leads for future re-engagement
- **CRM Sync** - Updates CRM with lead data

**Run:** `python examples/small_business/lead_qualification.py`

---

### 3. Content Moderation (`content_moderation.py`)
Review user-generated content for policy violations.

**Workers:**
- **Profanity Scanner** - Checks for banned words
- **Spam Detector** - Identifies spam patterns
- **Sentiment Analyzer** - Detects negative/toxic content
- **Decision Aggregator** - Combines analyses for final decision
- **Auto Approver** - Publishes clean content automatically
- **Review Queue** - Routes flagged content to humans

**Run:** `python examples/small_business/content_moderation.py`

---

### 4. Invoice Processing (`invoice_processing.py`)
Automate accounts payable with validation and approval routing.

**Workers:**
- **Data Extractor** - Parses invoice fields
- **Vendor Validator** - Checks approved vendor list
- **PO Validator** - Matches against purchase orders
- **Anomaly Detector** - Flags unusual amounts/patterns
- **Approval Router** - Determines approval level needed
- **Auto Approver** - Approves invoices under threshold
- **Payment Scheduler** - Schedules approved payments

**Run:** `python examples/small_business/invoice_processing.py`

---

### 5. AI-Powered Research Assistant (`research_assistant.py`)
Use Claude to research topics and generate summaries.

**Workers:**
- **Research Planner** - Creates research plan with Claude
- **Researcher** - Gathers information on sub-topics
- **Fact Checker** - Validates claims
- **Synthesizer** - Combines research into final report

**Run:** `python examples/small_business/research_assistant.py`

*Requires: `pip install anthills[claude]` and `ANTHROPIC_API_KEY` env var*

---

## Patterns Demonstrated

| Pattern | Examples |
|---------|----------|
| **Parallel Processing** | Multiple workers react to same pheromone |
| **Sequential Pipeline** | Data flows through stages (extract → validate → route) |
| **Conditional Routing** | Different paths based on payload values |
| **Aggregation** | Collect multiple signals before deciding |
| **Wildcard Subscription** | `ticket.*` catches all ticket events |
| **Auto-halt** | Colony stops when work is complete |

## Feature Ideas for Future Versions

Based on building these demos, here are features that would help:

1. **Persistent Board** - Redis/PostgreSQL backend for durable state
2. **Scheduled Triggers** - Cron-like pheromone deposits
3. **Batch Processing** - Efficient handling of many similar items
4. **Rate Limiting** - Control worker throughput
5. **Dead Letter Queue** - Handle failed pheromones
6. **Metrics Export** - Prometheus/StatsD integration
7. **Web Dashboard** - Visualize board state and worker activity
8. **Replay/Debug Mode** - Step through events for debugging
