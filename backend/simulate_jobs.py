"""
Periodically submits random HVAC service requests to the CoolFlow backend.

Usage:
    python -m backend.simulate_jobs
    python -m backend.simulate_jobs --interval 60   # every 60 seconds
"""

import argparse
import asyncio
import random
import urllib.request
import urllib.error
import json

CUSTOMERS = [
    ("Alice Thompson", "(555) 300-0001", "11 Birchwood Ln, Springfield"),
    ("Bob Nakamura",   "(555) 300-0002", "47 Cedar Blvd, Springfield"),
    ("Carmen Ortiz",   "(555) 300-0003", "88 Daisy Court, Springfield"),
    ("Derek Patel",    "(555) 300-0004", "200 Elm St, Springfield"),
    ("Eva Rossi",      "(555) 300-0005", "35 Fern Ave, Springfield"),
    ("Felix Grant",    "(555) 300-0006", "9 Gable Rd, Springfield"),
    ("Grace Liu",      "(555) 300-0007", "73 Harbor Dr, Springfield"),
    ("Henry Walsh",    "(555) 300-0008", "156 Ivy Pl, Springfield"),
    ("Irene Castillo", "(555) 300-0009", "22 Juniper Way, Springfield"),
    ("James Okafor",   "(555) 300-0010", "61 Kestrel Ct, Springfield"),
]

ISSUE_NOTES = {
    "AC": [
        "AC not blowing cold air — unit is running but warm.",
        "Thermostat set to 68°F but house won't cool below 78°F.",
        "Strange rattling noise from the outdoor condenser.",
        "AC trips the breaker after running for 10 minutes.",
    ],
    "Heating": [
        "Furnace kicks on but shuts off after 2 minutes.",
        "No heat in the master bedroom even with vents open.",
        "Pilot light keeps going out.",
        "Boiler making loud banging noises when it cycles.",
    ],
    "Maintenance": [
        "Annual HVAC checkup — system hasn't been serviced in 2 years.",
        "Filter replacement and duct inspection requested.",
        "Pre-winter tune-up for the heating system.",
        "Post-summer AC service before shutting down for the season.",
    ],
    "Emergency": [
        "Commercial refrigeration unit failed — business at risk.",
        "Complete HVAC failure in a nursing home — residents at risk.",
        "Gas smell near the furnace — need immediate inspection.",
        "Frozen pipes near the air handler — water damage risk.",
    ],
}

ISSUES   = list(ISSUE_NOTES.keys())
URGENCIES = ["low", "standard", "standard", "urgent", "emergency"]  # weighted


def random_job() -> dict:
    customer, phone, address = random.choice(CUSTOMERS)
    issue    = random.choice(ISSUES)
    urgency  = random.choice(URGENCIES)
    # Emergency issue always gets emergency urgency
    if issue == "Emergency":
        urgency = "emergency"
    notes = random.choice(ISSUE_NOTES[issue])
    return {
        "customer": customer,
        "phone":    phone,
        "address":  address,
        "issue":    issue,
        "urgency":  urgency,
        "notes":    notes,
    }


def post_job(payload: dict, url: str) -> str:
    body = json.dumps({"type": "job.requested", "payload": payload}).encode()
    req  = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            return result.get("id", "?")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Backend unreachable: {e.reason}") from e


async def run(interval: int, url: str):
    print(f"Job simulator started — posting every {interval}s to {url}")
    print("Press Ctrl+C to stop.\n")
    while True:
        job = random_job()
        try:
            pheromone_id = post_job(job, url)
            print(
                f"[+] Submitted  {job['issue']:12s} / {job['urgency']:9s} "
                f"for {job['customer']} → pheromone {pheromone_id}"
            )
        except ConnectionError as e:
            print(f"[!] {e}")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate periodic HVAC job submissions")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between jobs (default: 300)")
    parser.add_argument("--url", default="http://localhost:8000/api/deposit", help="Backend deposit URL")
    args = parser.parse_args()
    asyncio.run(run(args.interval, args.url))
