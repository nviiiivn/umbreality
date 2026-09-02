"""Real-world bounty program data gathering — read-only, inbound only.
Aggregates public info on bug bounty programs, security research opportunities."""

import json, urllib.request, datetime

KNOWN_PROGRAMS = {
    "hackerone": [
        {"name": "GitHub", "type": "web", "min_bounty": 500, "max_bounty": 30000},
        {"name": "Cloudflare", "type": "infra", "min_bounty": 200, "max_bounty": 20000},
        {"name": "Shopify", "type": "web", "min_bounty": 500, "max_bounty": 10000},
        {"name": "Discord", "type": "web", "min_bounty": 250, "max_bounty": 15000},
    ],
    "bugcrowd": [
        {"name": "Tesla", "type": "hardware", "min_bounty": 1000, "max_bounty": 10000},
        {"name": "Meta", "type": "web", "min_bounty": 500, "max_bounty": 40000},
    ]
}

def get_public_programs():
    """Return known public bounty programs (cached local data - no outbound)."""
    all_progs = []
    for platform, progs in KNOWN_PROGRAMS.items():
        for p in progs:
            all_progs.append({**p, "platform": platform})
    return {
        "count": len(all_progs),
        "programs": all_progs,
        "total_value_max": sum(p["max_bounty"] for p in all_progs),
        "scraped_at": str(datetime.datetime.now()),
    }

def recommend_for_company(company_name):
    """Match bounty program types to company capabilities."""
    matches = {
        "recon-inc": {"types": ["web", "infra"], "focus": "reconnaissance"},
        "exploit-inc": {"types": ["web", "api"], "focus": "exploitation"},
        "it-tools": {"types": ["infra", "mobile"], "focus": "tooling"},
    }
    return matches.get(company_name, {"types": ["web"], "focus": "general"})
