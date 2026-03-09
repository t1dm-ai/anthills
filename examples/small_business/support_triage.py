#!/usr/bin/env python3
"""
Customer Support Triage Demo

A small business receives support tickets via email/form. This colony:
1. Categorizes tickets (billing, technical, general)
2. Assigns priority (urgent, normal, low)
3. Drafts initial responses
4. Routes urgent issues to on-call

This demonstrates:
- Multiple workers reacting to the same pheromone
- Conditional routing based on pheromone payload
- Wildcard subscriptions for logging/monitoring
"""

import asyncio
from anthills import Colony, Pheromone


async def main():
    colony = Colony(name="support-triage", auto_halt=True, idle_timeout=1)
    
    # ==========================================================================
    # WORKER: Categorizer - Determines ticket category
    # ==========================================================================
    @colony.worker(reacts_to="ticket.received")
    async def categorize_ticket(ctx):
        """Analyze ticket and assign category."""
        ticket = ctx.pheromone.payload
        subject = ticket.get("subject", "").lower()
        body = ticket.get("body", "").lower()
        
        # Simple keyword-based categorization (would use LLM in production)
        if any(word in subject + body for word in ["bill", "payment", "charge", "invoice", "refund"]):
            category = "billing"
        elif any(word in subject + body for word in ["error", "bug", "broken", "crash", "not working"]):
            category = "technical"
        elif any(word in subject + body for word in ["cancel", "delete", "close account"]):
            category = "account"
        else:
            category = "general"
        
        print(f"📂 Categorized ticket as: {category}")
        
        await ctx.deposit(
            type="ticket.categorized",
            payload={
                **ticket,
                "category": category,
            },
        )
    
    # ==========================================================================
    # WORKER: Priority Scorer - Assigns urgency level
    # ==========================================================================
    @colony.worker(reacts_to="ticket.received")
    async def score_priority(ctx):
        """Analyze ticket and assign priority."""
        ticket = ctx.pheromone.payload
        subject = ticket.get("subject", "").lower()
        body = ticket.get("body", "").lower()
        
        # Check for urgency signals
        urgent_keywords = ["urgent", "asap", "immediately", "emergency", "critical", "down", "outage"]
        vip_domains = ["bigclient.com", "enterprise.io"]
        
        email = ticket.get("from_email", "")
        is_vip = any(domain in email for domain in vip_domains)
        has_urgent_words = any(word in subject + body for word in urgent_keywords)
        
        if is_vip or has_urgent_words:
            priority = "urgent"
        elif "please" in body and "soon" in body:
            priority = "normal"
        else:
            priority = "low"
        
        print(f"🎯 Assigned priority: {priority}" + (" ⭐ VIP" if is_vip else ""))
        
        await ctx.deposit(
            type="ticket.prioritized",
            payload={
                "ticket_id": ticket.get("id"),
                "priority": priority,
                "is_vip": is_vip,
            },
        )
    
    # ==========================================================================
    # WORKER: Urgent Router - Escalates urgent tickets
    # ==========================================================================
    @colony.worker(reacts_to="ticket.prioritized")
    async def route_urgent(ctx):
        """Route urgent tickets to on-call."""
        data = ctx.pheromone.payload
        
        if data.get("priority") == "urgent":
            print(f"🚨 URGENT: Routing ticket {data['ticket_id']} to on-call team!")
            
            await ctx.deposit(
                type="alert.oncall",
                payload={
                    "ticket_id": data["ticket_id"],
                    "reason": "urgent_priority",
                    "channel": "slack",  # Could integrate with Slack connector
                },
            )
    
    # ==========================================================================
    # WORKER: Response Drafter - Creates initial response
    # ==========================================================================
    @colony.worker(reacts_to="ticket.categorized")
    async def draft_response(ctx):
        """Draft an initial response based on category."""
        ticket = ctx.pheromone.payload
        category = ticket.get("category")
        
        # Template responses (would use LLM in production)
        templates = {
            "billing": "Thank you for contacting us about your billing inquiry. "
                      "I've forwarded this to our billing team who will review "
                      "your account and respond within 24 hours.",
            "technical": "Thank you for reporting this issue. Our technical team "
                        "is looking into it. Could you please provide any error "
                        "messages or screenshots that might help us diagnose the problem?",
            "account": "Thank you for reaching out about your account. We're sorry "
                      "to hear you're considering changes. A member of our team "
                      "will reach out to discuss your options.",
            "general": "Thank you for contacting us! We've received your message "
                      "and will get back to you as soon as possible.",
        }
        
        draft = templates.get(category, templates["general"])
        
        print(f"✍️  Drafted response for {category} ticket")
        
        await ctx.deposit(
            type="response.drafted",
            payload={
                "ticket_id": ticket.get("id"),
                "category": category,
                "draft": draft,
                "needs_review": category in ["account", "billing"],  # Human review for sensitive
            },
        )
    
    # ==========================================================================
    # WORKER: Metrics Collector - Tracks all ticket events
    # ==========================================================================
    @colony.worker(reacts_to="ticket.*")
    async def collect_metrics(ctx):
        """Log all ticket-related events for metrics."""
        print(f"📊 Metric: {ctx.pheromone.type} at {ctx.pheromone.deposited_at.isoformat()}")
    
    # ==========================================================================
    # WORKER: Response Reviewer - Checks if response needs human review
    # ==========================================================================
    @colony.worker(reacts_to="response.drafted")
    async def check_review_needed(ctx):
        """Route responses that need human review."""
        data = ctx.pheromone.payload
        
        if data.get("needs_review"):
            print(f"👀 Response for ticket {data['ticket_id']} queued for human review")
            await ctx.deposit(
                type="response.pending_review",
                payload=data,
            )
        else:
            print(f"✅ Response for ticket {data['ticket_id']} ready to send")
            await ctx.deposit(
                type="response.ready",
                payload=data,
            )
    
    # ==========================================================================
    # Simulate incoming tickets
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🎫 CUSTOMER SUPPORT TRIAGE DEMO")
    print("=" * 60 + "\n")
    
    # Ticket 1: Urgent billing issue from VIP
    colony.deposit(
        type="ticket.received",
        payload={
            "id": "TICKET-001",
            "from_email": "cfo@bigclient.com",
            "subject": "URGENT: Double charged on invoice",
            "body": "We were charged twice for our monthly subscription. Please fix ASAP!",
        },
    )
    
    # Ticket 2: Technical issue
    colony.deposit(
        type="ticket.received",
        payload={
            "id": "TICKET-002",
            "from_email": "user@example.com",
            "subject": "App not working",
            "body": "I'm getting an error when I try to log in. The page just shows a blank screen.",
        },
    )
    
    # Ticket 3: General question
    colony.deposit(
        type="ticket.received",
        payload={
            "id": "TICKET-003",
            "from_email": "curious@gmail.com",
            "subject": "Question about features",
            "body": "Hi, I was wondering if your product supports integrations with Zapier?",
        },
    )
    
    # Run the colony
    await colony.run_async()
    
    # Show final state
    print("\n" + "=" * 60)
    print("📋 FINAL BOARD STATE")
    print("=" * 60)
    
    for p in colony.board.read():
        print(f"  • {p.type}: {p.payload.get('ticket_id', p.payload.get('id', 'N/A'))}")


if __name__ == "__main__":
    asyncio.run(main())
