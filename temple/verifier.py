"""Local verification using Tower models — replaces paid Oracle for system checks."""

import json, urllib.request, os

TOWER = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
MODEL = "deepseek-r1:14b"  # Strongest reasoning model on Tower

def verify_system() -> dict:
    """Run a full system verification using Tower models. Zero cost."""
    # Gather system data
    checks = []
    
    # Check endpoints
    endpoints = [
        ("API Health", "http://localhost:8910/health", 200),
        ("Forum Stats", "http://localhost:8910/forum/stats", 200),
        ("Companies", "http://localhost:8910/temple/companies", 200),
        ("Dashboard", "http://localhost:8910/dashboard", 200),
        ("Messiah", "http://localhost:8910/messiah", 200),
        ("Fintech", "http://localhost:8910/fin/crypto", 200),
        ("Portfolio", "http://localhost:8910/sim/portfolio", 200),
    ]
    
    for name, url, expected in endpoints:
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            status = resp.status
            passed = status == expected
            checks.append({"check": name, "status": "PASS" if passed else "FAIL", "code": status})
        except Exception as e:
            checks.append({"check": name, "status": "ERROR", "detail": str(e)[:60]})
    
    passing = sum(1 for c in checks if c["status"] == "PASS")
    failing = sum(1 for c in checks if c["status"] != "PASS")
    
    # Let the Tower model analyze the results
    prompt = f"""System verification results: {passing} passing, {failing} failing out of {len(checks)} checks.
    
Failed checks: {[c for c in checks if c['status'] != 'PASS']}
    
Is the system healthy? What needs attention? Be brief and critical."""
    
    try:
        body = json.dumps({"model": MODEL, "messages": [
            {"role": "system", "content": "You are a system verifier. Be brief, be critical, be honest."},
            {"role": "user", "content": prompt}
        ], "stream": False, "options": {"num_predict": 200, "temperature": 0.1}}).encode()
        req = urllib.request.Request(f"{TOWER}/api/chat", data=body, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        verdict = resp.get("message", {}).get("content", "") or resp.get("message", {}).get("thinking", "")
    except:
        verdict = "Tower unreachable for analysis"
    
    return {
        "verified": failing == 0,
        "checks": checks,
        "summary": f"{passing}/{len(checks)} passing",
        "tower_analysis": verdict[:200],
        "verifier": f"Tower ({MODEL})",
    }
