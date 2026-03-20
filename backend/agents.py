"""
HVAC Colony agents for CoolFlow.

Pipeline:
  job.requested  →  LeadQualifier  →  job.qualified
  job.qualified  →  Dispatcher     →  job.dispatched
  job.dispatched →  TechSimulator  →  job.on_site
  job.on_site    →  JobCompleter   →  job.completed
  job.completed  →  InvoiceProcessor → invoice.ready
"""

import asyncio
import json
import random
from datetime import datetime, timezone

from anthills import Worker, WorkerContext
from anthills.integrations.claude import ClaudeWorker
from .ledger import current_entry


# ─── Instrumented Claude base ─────────────────────────────────────────────────

class InstrumentedClaudeWorker(ClaudeWorker):
    """
    ClaudeWorker that records every LLM call into the current ledger entry.
    Messages sent, raw response text, token usage, and model are all captured.
    """

    async def call_llm(self, messages: list[dict]):
        response = await super().call_llm(messages)
        entry = current_entry.get()
        if entry is not None:
            entry.messages = messages
            texts = [b.text for b in response.content if b.type == "text"]
            thinking = [b.thinking for b in response.content if b.type == "thinking"]
            entry.raw_response_text = "\n".join(texts)
            entry.thinking = thinking or None
            entry.token_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
            entry.model = response.model
        return response

# ─── Technician pool ──────────────────────────────────────────────────────────

TECHNICIANS = [
    {"id": "tech-1", "name": "Alex Rivera",    "specialties": ["AC", "Emergency"],                          "region": "North"},
    {"id": "tech-2", "name": "Maria Chen",     "specialties": ["Heating"],                                   "region": "South"},
    {"id": "tech-3", "name": "Marcus Johnson", "specialties": ["AC", "Heating", "Maintenance", "Emergency"], "region": "East"},
    {"id": "tech-4", "name": "Sarah Kim",      "specialties": ["Maintenance", "AC"],                        "region": "West"},
]

# In-memory availability — True = available
tech_availability: dict[str, bool] = {t["id"]: True for t in TECHNICIANS}


# ─── Agents ───────────────────────────────────────────────────────────────────

class LeadQualifier(InstrumentedClaudeWorker):
    """Uses Claude to assess and qualify incoming service requests."""

    reacts_to = "job.requested"
    output_pheromone_type = "job.qualified"
    model = "claude-haiku-4-5-20251001"
    system_prompt = (
        "You are an HVAC dispatch AI. Analyze incoming service requests and qualify them. "
        "Always respond with valid JSON only, no markdown, no extra text."
    )

    async def build_messages(self, pheromone):
        p = pheromone.payload
        return [{
            "role": "user",
            "content": (
                f"New HVAC service request:\n"
                f"- Customer: {p.get('customer')}\n"
                f"- Address: {p.get('address')}\n"
                f"- Issue: {p.get('issue')}\n"
                f"- Reported urgency: {p.get('urgency')}\n"
                f"- Notes: {p.get('notes', 'None provided')}\n\n"
                f"Qualify this request. Respond with JSON only:\n"
                f'{{"qualification_notes": "brief assessment of the issue", '
                f'"confirmed_urgency": "low|standard|urgent|emergency", '
                f'"priority_score": 7, '
                f'"recommended_action": "what the tech should do first"}}'
            ),
        }]

    async def parse_response(self, response, pheromone):
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        # Strip markdown code fences if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            qualification = json.loads(text)
        except Exception:
            qualification = {
                "qualification_notes": text[:200] or "Reviewed and approved.",
                "confirmed_urgency": pheromone.payload.get("urgency", "standard"),
                "priority_score": 5,
                "recommended_action": "Dispatch to next available technician.",
            }
        return {**pheromone.payload, **qualification}


class Dispatcher(Worker):
    """Assigns qualified jobs to the best available technician."""

    reacts_to = "job.qualified"

    async def handle(self, ctx: WorkerContext):
        p = ctx.pheromone.payload
        issue = p.get("issue", "")

        # Find best available tech — prefer specialty match
        assigned = None
        for tech in TECHNICIANS:
            if tech_availability.get(tech["id"]) and issue in tech["specialties"]:
                assigned = tech
                break

        # Fallback: any available tech
        if not assigned:
            for tech in TECHNICIANS:
                if tech_availability.get(tech["id"]):
                    assigned = tech
                    break

        if not assigned:
            # All techs busy — wait and re-queue
            await asyncio.sleep(20)
            ctx.deposit(type="job.qualified", payload=p)
            return

        tech_availability[assigned["id"]] = False
        ctx.deposit(
            type="job.dispatched",
            payload={
                **p,
                "tech_id": assigned["id"],
                "tech_name": assigned["name"],
                "tech_region": assigned["region"],
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
            },
        )


class TechSimulator(Worker):
    """Simulates a technician traveling to the job site."""

    reacts_to = "job.dispatched"
    max_concurrency = 10  # multiple jobs can travel simultaneously

    async def handle(self, ctx: WorkerContext):
        p = ctx.pheromone.payload
        urgency = p.get("confirmed_urgency") or p.get("urgency", "standard")

        travel_seconds = {
            "emergency": 8,
            "urgent":    14,
            "standard":  20,
            "low":       28,
        }.get(urgency, 20) + random.randint(0, 6)

        await asyncio.sleep(travel_seconds)

        ctx.deposit(
            type="job.on_site",
            payload={
                **p,
                "arrived_at": datetime.now(timezone.utc).isoformat(),
            },
        )


class JobCompleter(Worker):
    """Simulates a technician completing the job on site."""

    reacts_to = "job.on_site"
    max_concurrency = 10

    async def handle(self, ctx: WorkerContext):
        p = ctx.pheromone.payload
        issue = p.get("issue", "Maintenance")

        job_seconds = {
            "Emergency":   25,
            "AC":          35,
            "Heating":     40,
            "Maintenance": 30,
        }.get(issue, 30) + random.randint(0, 15)

        await asyncio.sleep(job_seconds)

        # Free the tech
        tech_id = p.get("tech_id")
        if tech_id:
            tech_availability[tech_id] = True

        ctx.deposit(
            type="job.completed",
            payload={
                **p,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "job_duration_seconds": job_seconds,
            },
        )


class InvoiceProcessor(InstrumentedClaudeWorker):
    """Uses Claude to generate an invoice estimate for a completed job."""

    reacts_to = "job.completed"
    output_pheromone_type = "invoice.ready"
    model = "claude-haiku-4-5-20251001"
    system_prompt = (
        "You are an HVAC billing AI. Generate invoice estimates for completed jobs. "
        "Always respond with valid JSON only, no markdown, no extra text."
    )

    async def build_messages(self, pheromone):
        p = pheromone.payload
        duration_min = round(p.get("job_duration_seconds", 30) / 60, 1)
        return [{
            "role": "user",
            "content": (
                f"HVAC job completed:\n"
                f"- Customer: {p.get('customer')}\n"
                f"- Issue type: {p.get('issue')}\n"
                f"- Notes: {p.get('notes', 'Standard service')}\n"
                f"- Duration: {duration_min} minutes\n"
                f"- Technician: {p.get('tech_name')}\n\n"
                f"Generate an invoice. Respond with JSON only:\n"
                f'{{"estimated_total": 175.00, '
                f'"line_items": [{{"description": "Labor", "amount": 125.00}}, {{"description": "Parts", "amount": 50.00}}], '
                f'"payment_terms": "Due upon receipt", '
                f'"warranty_notes": "any warranty info"}}'
            ),
        }]

    async def parse_response(self, response, pheromone):
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            invoice = json.loads(text)
        except Exception:
            invoice = {
                "estimated_total": 175.00,
                "line_items": [{"description": "HVAC Service", "amount": 175.00}],
                "payment_terms": "Due upon receipt",
                "warranty_notes": "",
            }
        return {**pheromone.payload, **invoice}
