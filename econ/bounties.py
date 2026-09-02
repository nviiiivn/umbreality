"""Bug bounty monitoring and aggregation for Sparks.
Scrapes public bug bounty data to identify opportunities."""

import json, subprocess, re
from datetime import datetime

def check_public_bounties():
    """Check known public bug bounty platforms for active programs."""
    platforms = [
        "https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/chaos-data/program-list.json",
    ]
    results = []
    for url in platforms:
        try:
            import urllib.request
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            programs = data.get("programs", data)[:20]
            for p in programs:
                results.append({
                    "name": p.get("name", "unknown"),
                    "platform": p.get("platform", "hackerone"),
                    "url": p.get("url", ""),
                    "bounty": p.get("bounty", True),
                    "detected_at": str(datetime.now()),
                })
        except Exception as e:
            results.append({"error": str(e), "platform": url[:50]})
    return {"count": len(results), "programs": results[:10]}


def analyze_bounty_fit(company_skills: list) -> dict:
    """Analyze which bounty types match a company's capabilities."""
    mappings = {
        "recon-inc": ["xss", "sqli", "subdomain takeover", "idor"],
        "exploit-inc": ["rce", "buffer overflow", "privilege escalation"],
        "it-tools": ["misconfiguration", "cors", "authentication bypass"],
    }
    return mappings
