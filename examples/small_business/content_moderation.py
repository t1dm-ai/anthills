#!/usr/bin/env python3
"""
Content Moderation Pipeline Demo

A small business with user-generated content (reviews, comments, posts).
This colony:
1. Scans content for prohibited patterns
2. Checks sentiment and toxicity
3. Auto-approves clean content
4. Queues flagged content for human review
5. Notifies users of decisions

This demonstrates:
- Parallel analysis (multiple workers analyze same content)
- Aggregation pattern (decision maker waits for analyses)
- Different outcomes based on combined signals
"""

import asyncio
import re
from anthills import Colony, Pheromone


async def main():
    colony = Colony(name="content-moderation", auto_halt=True, idle_timeout=1)
    
    # Track analysis results for aggregation
    analysis_results: dict[str, dict] = {}
    
    # ==========================================================================
    # WORKER: Profanity Scanner - Check for banned words
    # ==========================================================================
    @colony.worker(reacts_to="content.submitted")
    async def scan_profanity(ctx):
        """Scan content for profanity and banned words."""
        content = ctx.pheromone.payload
        text = content.get("text", "").lower()
        
        # Simple banned word list (would use proper filter in production)
        banned_words = ["spam", "scam", "fake"]  # Simplified for demo
        
        found_banned = [word for word in banned_words if word in text]
        
        result = {
            "content_id": content.get("id"),
            "check": "profanity",
            "passed": len(found_banned) == 0,
            "issues": found_banned,
        }
        
        print(f"🔍 Profanity check: {'✅ Clean' if result['passed'] else '❌ Found: ' + str(found_banned)}")
        
        await ctx.deposit(type="content.analysis.profanity", payload=result)
    
    # ==========================================================================
    # WORKER: Spam Detector - Check for spam patterns
    # ==========================================================================
    @colony.worker(reacts_to="content.submitted")
    async def detect_spam(ctx):
        """Detect spam patterns in content."""
        content = ctx.pheromone.payload
        text = content.get("text", "")
        
        spam_signals = []
        
        # Check for excessive caps
        if sum(1 for c in text if c.isupper()) / max(len(text), 1) > 0.5:
            spam_signals.append("excessive_caps")
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', text):
            spam_signals.append("repeated_chars")
        
        # Check for URLs
        if re.search(r'https?://|www\.', text.lower()):
            spam_signals.append("contains_url")
        
        # Check for phone numbers
        if re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', text):
            spam_signals.append("contains_phone")
        
        result = {
            "content_id": content.get("id"),
            "check": "spam",
            "passed": len(spam_signals) <= 1,  # Allow 1 signal
            "issues": spam_signals,
            "spam_score": len(spam_signals) * 25,  # 0-100
        }
        
        print(f"📧 Spam check: {'✅ Clean' if result['passed'] else '⚠️  Score: ' + str(result['spam_score'])}")
        
        await ctx.deposit(type="content.analysis.spam", payload=result)
    
    # ==========================================================================
    # WORKER: Sentiment Analyzer - Check tone and sentiment
    # ==========================================================================
    @colony.worker(reacts_to="content.submitted")
    async def analyze_sentiment(ctx):
        """Analyze content sentiment."""
        content = ctx.pheromone.payload
        text = content.get("text", "").lower()
        
        # Simple sentiment analysis (would use ML model in production)
        positive_words = ["great", "love", "excellent", "amazing", "wonderful", "fantastic", "good"]
        negative_words = ["hate", "terrible", "awful", "horrible", "worst", "bad", "disgusting"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        result = {
            "content_id": content.get("id"),
            "check": "sentiment",
            "sentiment": sentiment,
            "positive_signals": positive_count,
            "negative_signals": negative_count,
            "passed": sentiment != "negative" or negative_count < 3,
        }
        
        print(f"😊 Sentiment: {sentiment} (pos: {positive_count}, neg: {negative_count})")
        
        await ctx.deposit(type="content.analysis.sentiment", payload=result)
    
    # ==========================================================================
    # WORKER: Decision Aggregator - Combine all analyses
    # ==========================================================================
    @colony.worker(reacts_to="content.analysis.*")
    async def aggregate_decisions(ctx):
        """Aggregate analysis results and make final decision."""
        result = ctx.pheromone.payload
        content_id = result.get("content_id")
        check_type = result.get("check")
        
        # Store result
        if content_id not in analysis_results:
            analysis_results[content_id] = {}
        analysis_results[content_id][check_type] = result
        
        # Check if all analyses are complete
        required_checks = {"profanity", "spam", "sentiment"}
        completed_checks = set(analysis_results[content_id].keys())
        
        if completed_checks >= required_checks:
            # All checks done, make decision
            results = analysis_results[content_id]
            
            all_passed = all(r.get("passed", True) for r in results.values())
            
            issues = []
            for r in results.values():
                issues.extend(r.get("issues", []))
            
            if all_passed and not issues:
                decision = "approved"
                reason = "All checks passed"
            elif len(issues) <= 1:
                decision = "approved_with_warning"
                reason = f"Minor issues: {issues}"
            else:
                decision = "flagged_for_review"
                reason = f"Multiple issues: {issues}"
            
            print(f"\n📋 DECISION for {content_id}: {decision.upper()}")
            print(f"   Reason: {reason}")
            
            await ctx.deposit(
                type="content.decision",
                payload={
                    "content_id": content_id,
                    "decision": decision,
                    "reason": reason,
                    "checks": results,
                },
            )
            
            # Clean up
            del analysis_results[content_id]
    
    # ==========================================================================
    # WORKER: Auto Approver - Publish approved content
    # ==========================================================================
    @colony.worker(reacts_to="content.decision")
    async def auto_approve(ctx):
        """Auto-publish approved content."""
        data = ctx.pheromone.payload
        
        if data.get("decision") in ["approved", "approved_with_warning"]:
            print(f"✅ Publishing content {data['content_id']}")
            
            await ctx.deposit(
                type="content.published",
                payload={
                    "content_id": data["content_id"],
                    "auto_approved": True,
                },
            )
    
    # ==========================================================================
    # WORKER: Review Queue - Queue flagged content
    # ==========================================================================
    @colony.worker(reacts_to="content.decision")
    async def queue_for_review(ctx):
        """Queue flagged content for human review."""
        data = ctx.pheromone.payload
        
        if data.get("decision") == "flagged_for_review":
            print(f"👀 Queued content {data['content_id']} for human review")
            
            await ctx.deposit(
                type="review.queued",
                payload={
                    "content_id": data["content_id"],
                    "reason": data.get("reason"),
                    "priority": "normal",
                },
            )
    
    # ==========================================================================
    # Simulate content submissions
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🛡️  CONTENT MODERATION PIPELINE DEMO")
    print("=" * 60 + "\n")
    
    submissions = [
        {
            "id": "POST-001",
            "user_id": "user_123",
            "text": "I love this product! It's been amazing for our team. Highly recommend!",
            "type": "review",
        },
        {
            "id": "POST-002",
            "user_id": "user_456",
            "text": "THIS IS A SCAM!!! DON'T BUY!!! TERRIBLE TERRIBLE TERRIBLE!!!",
            "type": "review",
        },
        {
            "id": "POST-003",
            "user_id": "user_789",
            "text": "Pretty good product. Has some issues but overall works well.",
            "type": "review",
        },
        {
            "id": "POST-004",
            "user_id": "user_spam",
            "text": "CLICK HERE www.suspicious-link.com CALL NOW 555-123-4567 FREE MONEY!!!!!!",
            "type": "comment",
        },
    ]
    
    for sub in submissions:
        print(f"📝 Content: \"{sub['text'][:50]}...\"")
        colony.deposit(type="content.submitted", payload=sub)
        print()
    
    # Run the colony
    await colony.run_async()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MODERATION SUMMARY")
    print("=" * 60)
    
    decisions = colony.board.read(type="content.decision")
    for p in decisions:
        d = p.payload
        emoji = "✅" if "approved" in d["decision"] else "🔍"
        print(f"  {emoji} {d['content_id']}: {d['decision']}")


if __name__ == "__main__":
    asyncio.run(main())
