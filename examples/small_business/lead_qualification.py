#!/usr/bin/env python3
"""
Lead Qualification Pipeline Demo

A small B2B business receives leads from their website. This colony:
1. Enriches leads with company data
2. Scores leads based on criteria
3. Routes hot leads to sales immediately
4. Queues cold leads for nurture campaigns

This demonstrates:
- Sequential pipeline (enrichment → scoring → routing)
- Branching based on scores
- Integration points for external services
"""

import asyncio
import random
from anthills import Colony, Pheromone


async def main():
    colony = Colony(name="lead-qualification", auto_halt=True, idle_timeout=1)
    
    # ==========================================================================
    # WORKER: Lead Enricher - Fetches additional company data
    # ==========================================================================
    @colony.worker(reacts_to="lead.submitted")
    async def enrich_lead(ctx):
        """Enrich lead with company data (simulated API call)."""
        lead = ctx.pheromone.payload
        email = lead.get("email", "")
        domain = email.split("@")[-1] if "@" in email else ""
        
        # Simulate company lookup (would call Clearbit, Apollo, etc.)
        await asyncio.sleep(0.1)  # Simulate API latency
        
        # Mock enrichment data
        company_data = {
            "company_size": random.choice(["1-10", "11-50", "51-200", "201-500", "500+"]),
            "industry": random.choice(["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"]),
            "estimated_revenue": random.choice(["<$1M", "$1M-$10M", "$10M-$50M", "$50M+"]),
            "technologies": random.sample(["AWS", "Salesforce", "HubSpot", "Slack", "Jira"], k=2),
        }
        
        print(f"🔍 Enriched lead: {lead.get('name')} @ {domain}")
        print(f"   Company size: {company_data['company_size']}, Industry: {company_data['industry']}")
        
        await ctx.deposit(
            type="lead.enriched",
            payload={
                **lead,
                "domain": domain,
                "company": company_data,
            },
        )
    
    # ==========================================================================
    # WORKER: Lead Scorer - Calculates lead score
    # ==========================================================================
    @colony.worker(reacts_to="lead.enriched")
    async def score_lead(ctx):
        """Score lead based on fit criteria."""
        lead = ctx.pheromone.payload
        company = lead.get("company", {})
        
        score = 0
        reasons = []
        
        # Company size scoring
        size = company.get("company_size", "")
        if size in ["51-200", "201-500"]:
            score += 30
            reasons.append("ideal_company_size")
        elif size == "500+":
            score += 20
            reasons.append("enterprise")
        elif size == "11-50":
            score += 15
            reasons.append("smb")
        
        # Industry scoring
        industry = company.get("industry", "")
        if industry in ["Technology", "Finance"]:
            score += 25
            reasons.append("target_industry")
        elif industry in ["Healthcare"]:
            score += 15
            reasons.append("secondary_industry")
        
        # Revenue scoring
        revenue = company.get("estimated_revenue", "")
        if revenue in ["$10M-$50M", "$50M+"]:
            score += 25
            reasons.append("strong_revenue")
        elif revenue == "$1M-$10M":
            score += 10
            reasons.append("growing_revenue")
        
        # Technology fit
        techs = company.get("technologies", [])
        if "Salesforce" in techs or "HubSpot" in techs:
            score += 20
            reasons.append("crm_user")
        
        # Determine tier
        if score >= 70:
            tier = "hot"
        elif score >= 40:
            tier = "warm"
        else:
            tier = "cold"
        
        print(f"📊 Scored lead: {lead.get('name')} = {score} ({tier})")
        
        await ctx.deposit(
            type="lead.scored",
            payload={
                **lead,
                "score": score,
                "tier": tier,
                "score_reasons": reasons,
            },
        )
    
    # ==========================================================================
    # WORKER: Hot Lead Router - Immediate sales notification
    # ==========================================================================
    @colony.worker(reacts_to="lead.scored")
    async def route_hot_leads(ctx):
        """Route hot leads to sales team immediately."""
        lead = ctx.pheromone.payload
        
        if lead.get("tier") == "hot":
            print(f"🔥 HOT LEAD: {lead.get('name')} - Notifying sales!")
            
            await ctx.deposit(
                type="notification.sales",
                payload={
                    "channel": "slack",
                    "message": f"🔥 Hot lead: {lead.get('name')} ({lead.get('email')})",
                    "lead_id": lead.get("id"),
                    "score": lead.get("score"),
                    "urgency": "high",
                },
            )
            
            await ctx.deposit(
                type="lead.assigned",
                payload={
                    "lead_id": lead.get("id"),
                    "assigned_to": "sales_team",
                    "sla_hours": 1,  # Must contact within 1 hour
                },
            )
    
    # ==========================================================================
    # WORKER: Warm Lead Nurture - Queue for follow-up sequence
    # ==========================================================================
    @colony.worker(reacts_to="lead.scored")
    async def nurture_warm_leads(ctx):
        """Queue warm leads for nurture campaign."""
        lead = ctx.pheromone.payload
        
        if lead.get("tier") == "warm":
            print(f"☀️  Warm lead: {lead.get('name')} - Adding to nurture sequence")
            
            await ctx.deposit(
                type="campaign.enqueue",
                payload={
                    "lead_id": lead.get("id"),
                    "email": lead.get("email"),
                    "campaign": "warm_lead_nurture",
                    "delay_hours": 24,
                },
            )
    
    # ==========================================================================
    # WORKER: Cold Lead Archive - Store for future
    # ==========================================================================
    @colony.worker(reacts_to="lead.scored")
    async def archive_cold_leads(ctx):
        """Archive cold leads for future re-engagement."""
        lead = ctx.pheromone.payload
        
        if lead.get("tier") == "cold":
            print(f"❄️  Cold lead: {lead.get('name')} - Archived for later")
            
            await ctx.deposit(
                type="lead.archived",
                payload={
                    "lead_id": lead.get("id"),
                    "reason": "low_score",
                    "score": lead.get("score"),
                    "re_engage_after_days": 90,
                },
            )
    
    # ==========================================================================
    # WORKER: CRM Sync - Update CRM with all lead data
    # ==========================================================================
    @colony.worker(reacts_to="lead.scored")
    async def sync_to_crm(ctx):
        """Sync lead data to CRM."""
        lead = ctx.pheromone.payload
        
        # Simulate CRM API call
        print(f"💾 Syncing {lead.get('name')} to CRM (score: {lead.get('score')}, tier: {lead.get('tier')})")
        
        await ctx.deposit(
            type="crm.synced",
            payload={
                "lead_id": lead.get("id"),
                "crm_id": f"CRM-{random.randint(10000, 99999)}",
                "synced_fields": ["score", "tier", "company", "score_reasons"],
            },
        )
    
    # ==========================================================================
    # Simulate incoming leads
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🎯 LEAD QUALIFICATION PIPELINE DEMO")
    print("=" * 60 + "\n")
    
    leads = [
        {
            "id": "LEAD-001",
            "name": "Sarah Chen",
            "email": "sarah@techstartup.io",
            "source": "demo_request",
            "message": "Interested in enterprise plan",
        },
        {
            "id": "LEAD-002",
            "name": "Bob Smith",
            "email": "bob@smallbiz.com",
            "source": "whitepaper_download",
            "message": "Downloaded pricing guide",
        },
        {
            "id": "LEAD-003",
            "name": "Alice Johnson",
            "email": "alice@bigcorp.com",
            "source": "webinar_signup",
            "message": "Attended product demo webinar",
        },
    ]
    
    for lead in leads:
        print(f"📥 New lead: {lead['name']} ({lead['email']})")
        colony.deposit(type="lead.submitted", payload=lead)
    
    print("\n" + "-" * 40 + "\n")
    
    # Run the colony
    await colony.run_async()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PIPELINE SUMMARY")
    print("=" * 60)
    
    scored = colony.board.read(type="lead.scored")
    for p in scored:
        lead = p.payload
        print(f"  • {lead['name']}: {lead['tier'].upper()} (score: {lead['score']})")


if __name__ == "__main__":
    asyncio.run(main())
