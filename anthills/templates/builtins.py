"""
Built-in Colony Templates.

These templates ship with Anthills Cloud and demonstrate common use cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    ColonyTemplate,
    WorkerSpec,
    TriggerSpec,
    ParameterSpec,
)

if TYPE_CHECKING:
    from .catalog import TemplateCatalog


# Customer Inquiry Responder Template
CUSTOMER_INQUIRY_RESPONDER = ColonyTemplate(
    template_id="customer-inquiry-responder",
    name="Customer Inquiry Responder",
    description="Monitors your inbox and drafts replies to customer questions using your business context.",
    category="customer-support",
    version="1.0.0",
    author="anthills",
    icon="📧",
    estimated_cost_per_run="~$0.03 per email",
    required_connectors=["gmail"],
    parameters=[
        ParameterSpec(
            name="business_name",
            display_name="Business Name",
            description="Your business name, used when signing replies.",
            type="string",
        ),
        ParameterSpec(
            name="business_context",
            display_name="About Your Business",
            description="A brief description of what your business does, your products, and your policies.",
            type="string",
        ),
        ParameterSpec(
            name="reply_tone",
            display_name="Reply Tone",
            description="How should replies sound?",
            type="select",
            options=["Professional", "Friendly", "Concise"],
            default="Friendly",
        ),
        ParameterSpec(
            name="human_review",
            display_name="Require human approval before sending?",
            description="If yes, replies are drafted and held for your approval.",
            type="boolean",
            default=True,
        ),
    ],
    triggers=[
        TriggerSpec(
            type="connector_event",
            config={"connector": "gmail", "event": "email.received"},
        )
    ],
    workers=[
        WorkerSpec(
            id="classifier",
            name="Inquiry Classifier",
            type="claude",
            reacts_to=["email.received"],
            output_pheromone_type="inquiry.classified",
            system_prompt=(
                "You classify incoming emails for {business_name}. "
                "Determine if the email is a customer inquiry requiring a response, "
                "spam, or an internal email. "
                "Respond only with JSON: {{\"type\": \"inquiry|spam|internal\", \"summary\": \"one sentence\"}}"
            ),
            prompt_template="Classify this email:\n\nFrom: {sender}\nSubject: {subject}\nBody: {body}",
            connectors=[],
        ),
        WorkerSpec(
            id="responder",
            name="Reply Drafter",
            type="claude",
            reacts_to=["inquiry.classified"],
            output_pheromone_type="reply.drafted",
            system_prompt=(
                "You are a {reply_tone} customer support assistant for {business_name}. "
                "Context about the business: {business_context}. "
                "Draft a helpful, accurate reply to the customer inquiry. "
                "Sign off as '{business_name} Support Team'."
            ),
            prompt_template="Draft a reply to this customer inquiry:\n\n{summary}\n\nOriginal email body:\n{body}",
            connectors=["gmail"],
        ),
    ],
    tags=["email", "customer-support", "auto-reply"],
)


# Weekly Sales Summary Template
WEEKLY_SALES_SUMMARY = ColonyTemplate(
    template_id="weekly-sales-summary",
    name="Weekly Sales Summary",
    description="Generates a weekly sales summary from your Shopify or Stripe data and posts to Slack.",
    category="sales",
    version="1.0.0",
    author="anthills",
    icon="📊",
    estimated_cost_per_run="~$0.05 per report",
    required_connectors=["slack"],  # shopify in Phase 2
    parameters=[
        ParameterSpec(
            name="slack_channel",
            display_name="Slack Channel",
            description="Which channel should receive the weekly summary?",
            type="string",
            default="#sales",
        ),
        ParameterSpec(
            name="report_day",
            display_name="Report Day",
            description="Which day should the report be generated?",
            type="select",
            options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default="Monday",
        ),
        ParameterSpec(
            name="include_top_products",
            display_name="Include top products?",
            description="Include a list of best-selling products in the summary.",
            type="boolean",
            default=True,
        ),
    ],
    triggers=[
        TriggerSpec(
            type="schedule",
            config={"cron": "0 9 * * MON"},  # 9 AM on Mondays
        )
    ],
    workers=[
        WorkerSpec(
            id="data_collector",
            name="Sales Data Collector",
            type="webhook",  # Placeholder for actual data collection
            reacts_to=["schedule.triggered"],
            output_pheromone_type="sales.data_collected",
            system_prompt="",
            prompt_template="",
            connectors=[],
        ),
        WorkerSpec(
            id="summarizer",
            name="Summary Generator",
            type="claude",
            reacts_to=["sales.data_collected"],
            output_pheromone_type="summary.generated",
            system_prompt=(
                "You are a sales analyst. Generate a concise, actionable weekly sales summary. "
                "Highlight key metrics: total revenue, order count, average order value. "
                "Note any significant trends or anomalies."
            ),
            prompt_template="Generate a weekly sales summary from this data:\n\n{sales_data}",
            connectors=[],
        ),
        WorkerSpec(
            id="poster",
            name="Slack Poster",
            type="claude",
            reacts_to=["summary.generated"],
            output_pheromone_type="summary.posted",
            system_prompt=(
                "Format the sales summary for Slack. Use appropriate emoji and formatting. "
                "Keep it professional but engaging."
            ),
            prompt_template="Format this summary for Slack posting:\n\n{summary}",
            connectors=["slack"],
        ),
    ],
    tags=["sales", "reporting", "slack", "weekly"],
)


# Research Assistant Template
RESEARCH_ASSISTANT = ColonyTemplate(
    template_id="research-assistant",
    name="Research Assistant",
    description="A multi-agent research pipeline that investigates topics and synthesizes findings.",
    category="research",
    version="1.0.0",
    author="anthills",
    icon="🔬",
    estimated_cost_per_run="~$0.10 per topic",
    required_connectors=[],
    parameters=[
        ParameterSpec(
            name="research_depth",
            display_name="Research Depth",
            description="How thorough should the research be?",
            type="select",
            options=["Quick Overview", "Standard", "Deep Dive"],
            default="Standard",
        ),
        ParameterSpec(
            name="output_format",
            display_name="Output Format",
            description="How should findings be formatted?",
            type="select",
            options=["Bullet Points", "Full Report", "Executive Summary"],
            default="Executive Summary",
        ),
    ],
    triggers=[
        TriggerSpec(type="manual"),
    ],
    workers=[
        WorkerSpec(
            id="researcher",
            name="Topic Researcher",
            type="claude",
            reacts_to=["topic.queued"],
            output_pheromone_type="research.complete",
            system_prompt=(
                "You are a thorough researcher. Research depth: {research_depth}. "
                "Investigate the given topic and provide comprehensive findings. "
                "Include key facts, recent developments, and notable perspectives."
            ),
            prompt_template="Research this topic thoroughly:\n\n{topic}",
            connectors=[],
        ),
        WorkerSpec(
            id="synthesizer",
            name="Findings Synthesizer",
            type="claude",
            reacts_to=["research.complete"],
            output_pheromone_type="synthesis.complete",
            system_prompt=(
                "You are an expert at synthesizing research findings. "
                "Output format: {output_format}. "
                "Combine multiple research results into a coherent narrative."
            ),
            prompt_template="Synthesize these research findings:\n\n{findings}",
            connectors=[],
        ),
    ],
    tags=["research", "analysis", "synthesis"],
)


# All built-in templates
BUILTIN_TEMPLATES = [
    CUSTOMER_INQUIRY_RESPONDER,
    WEEKLY_SALES_SUMMARY,
    RESEARCH_ASSISTANT,
]


def register_builtins(catalog: "TemplateCatalog") -> None:
    """Register all built-in templates with a catalog."""
    for template in BUILTIN_TEMPLATES:
        catalog.register(template)
