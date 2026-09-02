"""System Maintenance — retention policy, integrity checks, data pruning.
Run periodically (e.g., daily via cron) to keep the system healthy."""

import sqlite3, os, hashlib, datetime, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPORTS_DIR = BASE / "logs" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATHS = {
    "forum": BASE / "forum" / "forum.db",
    "knowledge": BASE / "companies" / "research_corp" / "knowledge" / "knowledge.db",
    "throne": BASE / "temple" / "throne_perf.db",
    "ascension": BASE / "sub_stack" / "ascension.db",
    "audit": BASE / "audit.db",
    "guide": BASE / "temple" / "guide.db",
}


def check_integrity() -> dict:
    """Run SQLite integrity_check on all databases."""
    results = {}
    for name, path in DB_PATHS.items():
        if not path.exists():
            results[name] = {"status": "not_found", "size": 0}
            continue
        size = path.stat().st_size
        try:
            conn = sqlite3.connect(str(path))
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            conn.close()
            results[name] = {
                "status": "ok" if integrity == "ok" else "corrupt",
                "size_kb": round(size / 1024, 1),
                "integrity": integrity,
            }
        except Exception as e:
            results[name] = {"status": "error", "error": str(e), "size_kb": round(size / 1024, 1)}
    return results


def compute_checksums() -> dict:
    """Compute SHA256 checksums for all databases."""
    checksums = {}
    for name, path in DB_PATHS.items():
        if path.exists():
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            checksums[name] = h
    return checksums


def apply_retention_policy(keep_findings_days: int = 90, keep_threads_days: int = 365) -> dict:
    """Archive or prune old data according to retention policy."""
    results = {"pruned": {}, "archived": {}}
    
    # Prune old audit log entries (keep 30 days)
    audit_path = DB_PATHS.get("audit")
    if audit_path and audit_path.exists():
        conn = sqlite3.connect(str(audit_path))
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        count = conn.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,)).rowcount
        conn.commit()
        conn.close()
        results["pruned"]["audit_entries"] = count
    
    # Archive old findings from knowledge base
    kb_path = DB_PATHS.get("knowledge")
    if kb_path and kb_path.exists():
        conn = sqlite3.connect(str(kb_path))
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=keep_findings_days)).isoformat()
        old = conn.execute("SELECT COUNT(*) FROM findings WHERE created_at < ?", (cutoff,)).fetchone()[0]
        # For now just count — actual archiving would dump to file
        results["archived"]["old_findings"] = old
        conn.close()
    
    # Vacuum databases to reclaim space
    for name, path in DB_PATHS.items():
        if path.exists():
            try:
                conn = sqlite3.connect(str(path))
                conn.execute("VACUUM")
                conn.close()
                results["pruned"][f"{name}_vacuumed"] = True
            except:
                pass
    
    return results


def generate_report() -> str:
    """Generate a maintenance report."""
    integrity = check_integrity()
    checksums = compute_checksums()
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = REPORTS_DIR / f"maintenance_{timestamp}.json"
    
    # Collect DB sizes
    sizes = {}
    for name, path in DB_PATHS.items():
        if path.exists():
            sizes[name] = path.stat().st_size // 1024
    
    report = {
        "timestamp": timestamp,
        "integrity": integrity,
        "checksums": checksums,
        "db_sizes_kb": sizes,
        "total_size_kb": sum(sizes.values()),
    }
    
    report_path.write_text(__import__("json").dumps(report, indent=2))
    return str(report_path)


if __name__ == "__main__":
    import json
    print("=== Integrity Check ===")
    integrity = check_integrity()
    for name, result in integrity.items():
        status_icon = "✅" if result.get("status") == "ok" else "❌" if result.get("status") == "corrupt" else "⚠️"
        print(f"  {status_icon} {name}: {result.get('status')} ({result.get('size_kb', '?')} KB)")
    
    print("\n=== Retention Policy ===")
    retention = apply_retention_policy()
    print(f"  Pruned: {retention['pruned']}")
    
    print("\n=== Report ===")
    report_path = generate_report()
    print(f"  Saved to: {report_path}")
