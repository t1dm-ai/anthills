#!/usr/bin/env python3
"""
Invoice Processing Pipeline Demo

A small business receives invoices from vendors. This colony:
1. Extracts key data from invoice
2. Validates against PO and budget
3. Detects anomalies (unusual amounts, new vendors)
4. Routes for appropriate approval
5. Schedules payment

This demonstrates:
- Data extraction and validation
- Business rule enforcement
- Multi-level approval routing
- Integration with accounting systems
"""

import asyncio
from datetime import datetime, timedelta
from anthills import Colony, Pheromone


async def main():
    colony = Colony(name="invoice-processing", auto_halt=True, idle_timeout=1)
    
    # Mock database of approved vendors and POs
    APPROVED_VENDORS = {
        "ACME Corp": {"id": "V001", "avg_invoice": 5000, "payment_terms": 30},
        "Office Supplies Inc": {"id": "V002", "avg_invoice": 500, "payment_terms": 15},
        "Cloud Services LLC": {"id": "V003", "avg_invoice": 2000, "payment_terms": 30},
    }
    
    PURCHASE_ORDERS = {
        "PO-2024-001": {"vendor": "ACME Corp", "amount": 10000, "remaining": 7500},
        "PO-2024-002": {"vendor": "Office Supplies Inc", "amount": 2000, "remaining": 1500},
        "PO-2024-003": {"vendor": "Cloud Services LLC", "amount": 5000, "remaining": 3000},
    }
    
    APPROVAL_THRESHOLDS = {
        "auto": 500,        # Auto-approve under $500
        "manager": 5000,    # Manager approval up to $5000
        "director": 25000,  # Director approval up to $25000
        "cfo": float('inf') # CFO for anything above
    }
    
    # ==========================================================================
    # WORKER: Data Extractor - Parse invoice data
    # ==========================================================================
    @colony.worker(reacts_to="invoice.received")
    async def extract_invoice_data(ctx):
        """Extract and normalize invoice data."""
        invoice = ctx.pheromone.payload
        
        # In production, would use OCR/AI to extract from PDF
        # For demo, data is already structured
        
        extracted = {
            "invoice_id": invoice.get("invoice_number"),
            "vendor_name": invoice.get("vendor"),
            "amount": invoice.get("amount"),
            "currency": invoice.get("currency", "USD"),
            "po_number": invoice.get("po_reference"),
            "invoice_date": invoice.get("date"),
            "due_date": invoice.get("due_date"),
            "line_items": invoice.get("items", []),
            "extraction_confidence": 0.95,  # OCR confidence
        }
        
        print(f"📄 Extracted: Invoice {extracted['invoice_id']} from {extracted['vendor_name']}")
        print(f"   Amount: ${extracted['amount']:,.2f}")
        
        await ctx.deposit(type="invoice.extracted", payload=extracted)
    
    # ==========================================================================
    # WORKER: Vendor Validator - Check if vendor is approved
    # ==========================================================================
    @colony.worker(reacts_to="invoice.extracted")
    async def validate_vendor(ctx):
        """Validate vendor is in approved list."""
        invoice = ctx.pheromone.payload
        vendor_name = invoice.get("vendor_name")
        
        vendor_info = APPROVED_VENDORS.get(vendor_name)
        
        if vendor_info:
            result = {
                "invoice_id": invoice.get("invoice_id"),
                "check": "vendor",
                "passed": True,
                "vendor_id": vendor_info["id"],
                "payment_terms": vendor_info["payment_terms"],
            }
            print(f"✅ Vendor validated: {vendor_name}")
        else:
            result = {
                "invoice_id": invoice.get("invoice_id"),
                "check": "vendor",
                "passed": False,
                "issue": "unknown_vendor",
                "vendor_name": vendor_name,
            }
            print(f"⚠️  Unknown vendor: {vendor_name}")
        
        await ctx.deposit(type="invoice.validation.vendor", payload=result)
    
    # ==========================================================================
    # WORKER: PO Validator - Match against purchase order
    # ==========================================================================
    @colony.worker(reacts_to="invoice.extracted")
    async def validate_po(ctx):
        """Validate invoice matches purchase order."""
        invoice = ctx.pheromone.payload
        po_number = invoice.get("po_number")
        amount = invoice.get("amount", 0)
        
        po = PURCHASE_ORDERS.get(po_number) if po_number else None
        
        if not po_number:
            result = {
                "invoice_id": invoice.get("invoice_id"),
                "check": "po",
                "passed": False,
                "issue": "missing_po",
            }
            print(f"⚠️  No PO reference provided")
        elif not po:
            result = {
                "invoice_id": invoice.get("invoice_id"),
                "check": "po",
                "passed": False,
                "issue": "invalid_po",
                "po_number": po_number,
            }
            print(f"⚠️  Invalid PO: {po_number}")
        elif amount > po["remaining"]:
            result = {
                "invoice_id": invoice.get("invoice_id"),
                "check": "po",
                "passed": False,
                "issue": "exceeds_po_balance",
                "po_number": po_number,
                "invoice_amount": amount,
                "po_remaining": po["remaining"],
            }
            print(f"⚠️  Invoice ${amount:,.2f} exceeds PO balance ${po['remaining']:,.2f}")
        else:
            result = {
                "invoice_id": invoice.get("invoice_id"),
                "check": "po",
                "passed": True,
                "po_number": po_number,
                "po_remaining_after": po["remaining"] - amount,
            }
            print(f"✅ PO validated: {po_number}")
        
        await ctx.deposit(type="invoice.validation.po", payload=result)
    
    # ==========================================================================
    # WORKER: Anomaly Detector - Flag unusual invoices
    # ==========================================================================
    @colony.worker(reacts_to="invoice.extracted")
    async def detect_anomalies(ctx):
        """Detect anomalies in invoice."""
        invoice = ctx.pheromone.payload
        vendor_name = invoice.get("vendor_name")
        amount = invoice.get("amount", 0)
        
        anomalies = []
        
        # Check against vendor average
        vendor_info = APPROVED_VENDORS.get(vendor_name)
        if vendor_info:
            avg = vendor_info["avg_invoice"]
            if amount > avg * 2:
                anomalies.append({
                    "type": "high_amount",
                    "message": f"Amount ${amount:,.2f} is {amount/avg:.1f}x typical (${avg:,.2f})",
                })
        
        # Check for round numbers (potential fraud signal)
        if amount >= 1000 and amount % 1000 == 0:
            anomalies.append({
                "type": "round_number",
                "message": f"Suspiciously round amount: ${amount:,.2f}",
            })
        
        result = {
            "invoice_id": invoice.get("invoice_id"),
            "check": "anomaly",
            "passed": len(anomalies) == 0,
            "anomalies": anomalies,
        }
        
        if anomalies:
            print(f"🚨 Anomalies detected:")
            for a in anomalies:
                print(f"   - {a['message']}")
        else:
            print(f"✅ No anomalies detected")
        
        await ctx.deposit(type="invoice.validation.anomaly", payload=result)
    
    # ==========================================================================
    # WORKER: Approval Router - Determine approval path
    # ==========================================================================
    validation_results: dict[str, dict] = {}
    
    @colony.worker(reacts_to="invoice.validation.*")
    async def aggregate_validations(ctx):
        """Aggregate validations and route for approval."""
        result = ctx.pheromone.payload
        invoice_id = result.get("invoice_id")
        check_type = result.get("check")
        
        # Store result
        if invoice_id not in validation_results:
            validation_results[invoice_id] = {"checks": {}, "invoice": None}
        validation_results[invoice_id]["checks"][check_type] = result
        
        # Check if all validations complete
        required_checks = {"vendor", "po", "anomaly"}
        completed = set(validation_results[invoice_id]["checks"].keys())
        
        if completed >= required_checks:
            checks = validation_results[invoice_id]["checks"]
            
            # Get original invoice amount from board
            invoices = ctx.board.read(type="invoice.extracted")
            invoice = next((i.payload for i in invoices if i.payload.get("invoice_id") == invoice_id), {})
            amount = invoice.get("amount", 0)
            
            all_passed = all(c.get("passed", False) for c in checks.values())
            has_anomalies = not checks.get("anomaly", {}).get("passed", True)
            
            # Determine approval level needed
            if not all_passed:
                approval_level = "manual_review"
                reason = "Validation failures"
            elif has_anomalies:
                approval_level = "manager"  # Bump up for anomalies
                reason = "Anomalies detected"
            elif amount <= APPROVAL_THRESHOLDS["auto"]:
                approval_level = "auto"
                reason = f"Under auto-approval threshold (${APPROVAL_THRESHOLDS['auto']})"
            elif amount <= APPROVAL_THRESHOLDS["manager"]:
                approval_level = "manager"
                reason = f"Under manager threshold (${APPROVAL_THRESHOLDS['manager']:,})"
            elif amount <= APPROVAL_THRESHOLDS["director"]:
                approval_level = "director"
                reason = f"Under director threshold (${APPROVAL_THRESHOLDS['director']:,})"
            else:
                approval_level = "cfo"
                reason = "Exceeds director threshold"
            
            print(f"\n📋 ROUTING: Invoice {invoice_id}")
            print(f"   Amount: ${amount:,.2f}")
            print(f"   Approval needed: {approval_level.upper()}")
            print(f"   Reason: {reason}")
            
            await ctx.deposit(
                type="invoice.routed",
                payload={
                    "invoice_id": invoice_id,
                    "amount": amount,
                    "approval_level": approval_level,
                    "reason": reason,
                    "validations_passed": all_passed,
                    "checks": checks,
                },
            )
            
            del validation_results[invoice_id]
    
    # ==========================================================================
    # WORKER: Auto Approver - Process auto-approved invoices
    # ==========================================================================
    @colony.worker(reacts_to="invoice.routed")
    async def auto_approve(ctx):
        """Auto-approve eligible invoices."""
        data = ctx.pheromone.payload
        
        if data.get("approval_level") == "auto":
            print(f"✅ AUTO-APPROVED: Invoice {data['invoice_id']}")
            
            await ctx.deposit(
                type="invoice.approved",
                payload={
                    "invoice_id": data["invoice_id"],
                    "approved_by": "system",
                    "approval_type": "auto",
                },
            )
    
    # ==========================================================================
    # WORKER: Payment Scheduler - Schedule approved payments
    # ==========================================================================
    @colony.worker(reacts_to="invoice.approved")
    async def schedule_payment(ctx):
        """Schedule payment for approved invoice."""
        data = ctx.pheromone.payload
        invoice_id = data.get("invoice_id")
        
        # Calculate payment date (would use vendor terms)
        payment_date = datetime.now() + timedelta(days=30)
        
        print(f"💰 Payment scheduled: Invoice {invoice_id} on {payment_date.strftime('%Y-%m-%d')}")
        
        await ctx.deposit(
            type="payment.scheduled",
            payload={
                "invoice_id": invoice_id,
                "payment_date": payment_date.isoformat(),
                "status": "pending",
            },
        )
    
    # ==========================================================================
    # Simulate incoming invoices
    # ==========================================================================
    print("\n" + "=" * 60)
    print("📑 INVOICE PROCESSING PIPELINE DEMO")
    print("=" * 60 + "\n")
    
    invoices = [
        {
            "invoice_number": "INV-2024-001",
            "vendor": "Office Supplies Inc",
            "amount": 350.00,
            "po_reference": "PO-2024-002",
            "date": "2024-01-15",
            "due_date": "2024-01-30",
            "items": [{"desc": "Paper", "qty": 50, "price": 7.00}],
        },
        {
            "invoice_number": "INV-2024-002",
            "vendor": "ACME Corp",
            "amount": 15000.00,
            "po_reference": "PO-2024-001",
            "date": "2024-01-16",
            "due_date": "2024-02-15",
            "items": [{"desc": "Equipment", "qty": 1, "price": 15000.00}],
        },
        {
            "invoice_number": "INV-2024-003",
            "vendor": "Unknown Vendor Co",
            "amount": 5000.00,
            "po_reference": None,
            "date": "2024-01-17",
            "due_date": "2024-02-16",
            "items": [{"desc": "Services", "qty": 1, "price": 5000.00}],
        },
    ]
    
    for inv in invoices:
        print(f"📥 Received: {inv['invoice_number']} from {inv['vendor']} - ${inv['amount']:,.2f}")
        colony.deposit(type="invoice.received", payload=inv)
        print()
    
    # Run the colony
    await colony.run_async()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    routed = colony.board.read(type="invoice.routed")
    for p in routed:
        r = p.payload
        status = "✅" if r.get("validations_passed") else "⚠️"
        print(f"  {status} {r['invoice_id']}: ${r['amount']:,.2f} → {r['approval_level'].upper()}")


if __name__ == "__main__":
    asyncio.run(main())
