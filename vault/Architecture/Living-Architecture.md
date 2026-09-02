# Living Architecture

> *What's actually running right now — not the ideal, but the deployed.*

---

## Network Topology

```
                         alola.lol
                    (Cloudflare Tunnel)
                          │
                     ┌────┴────┐
                     │  CADDY  │  (:8081)
                     │ (router)│
                     └────┬────┘
                          │
          ┌───────────────┼───────────────────┐
          │               │                   │
   ┌──────┴──────┐  ┌─────┴──────┐  ┌────────┴────────┐
   │  ai-tp .21  │  │ lil faeg. │  │   Tower .24     │
   │  (RPi 5)    │  │  .20      │  │  (RTX 3080)     │
   │             │  │           │  │                 │
   │ Caddy :8081 │  │ Navidrome │  │ Ollama server   │
   │ Worker API  │  │ Uptime    │  │  15+ models     │
   │ Temple      │  │ Kuma      │  │ dolphin3:8b     │
   │ Companies   │  │ AdGuard   │  │ deepseek-r1:14b │
   │ Forum DB    │  │           │  │ qwen3.5:9b      │
   │ MkDocs Wiki │  │           │  │ gemma4          │
   └─────────────┘  └───────────┘  └─────────────────┘
```

## Layer Implementation Status

| Layer | Name | Status | Key Components |
|:------|:-----|:-------|:---------------|
| 0 | God(s) | ✅ Live | admin.alola.lol — Metatron |
| 0.5 | Avatar | ✅ Live | Secret Councils, 13 Messengers |
| 1 | Illuminati | ✅ Live | Intent interpreter, ACP protocol |
| 2 | Messiah | ✅ Live | Constitution, Master Goal, company charters |
| 3 | Temple | ✅ Live | Registry, Allocator, Overseer, Scheduler, Guide |
| 4 | Throne | ✅ Live | 6-dimension validation, ascension pipeline, factions |
| 5 | Companies | ✅ Live | 14 companies, each with sub-stack |
| 6 | Workers | ✅ Live | 5 worker modules (researcher, analyst, coder, reporter, base) |

## What's New This Session

### Sub-Stacks (`sub_stack/`)
Every company now has its own internal stack:
- **Sub-Throne** — internal quality gate, tracks creativity + quality per company
- **Sub-Messiah** — unique company charter and philosophy
- **Sub-Temple** — internal resource tracking (creative vs maintenance cycles)
- **Sub-Illuminati** — internal observation, drift detection, alignment tracking

### Ascension (`sub_stack/ascension.py`)
4 pathways with SQLite persistence: Monastery 🕯️, Coliseum ⚔️, Academy 📖, Commerce 💰
Each with 5 stations, milestone tracking, affinity scoring.

### Creative Pipeline (`creative/pipeline/`)
Expression pipeline — any text input generates deterministic music (WAV) or visual art (SVG).

### Tool Registry (`creative/tool_registry.py`)
6 built-in tools, agents can search, discover, and register new ones.

### Defense
- API key auth on all POST/PUT/DELETE endpoints
- Rate limiting (30 req/60s per IP)
- Input sanitization on 15+ endpoints
- CORS restricted to *.alola.lol
- Persistent audit log in SQLite

### Data Integrity
- `maintenance.py` — PRAGMA integrity_check, SHA256 checksums, DB vacuum
- `backup.sh` — Daily cron, 14-day retention, integrity-verified backups
- Retention policy: 30d audit logs, 90d findings, 365d threads

### Progress Guide (`temple/guide.py`)
Learning loops — Throne adjusts thresholds based on history, scheduler learns company affinities, Messiah version tracking.

### Portfolio (`sim/persistent_portfolio.py`)
SQLite-backed trade history with real day-over-day P&L tracking (not random rerolls).

## All Endpoints

The full API now has 90+ routes across system, temple, forum, throne, messiah, ascension, tools, creative, simulation, fintech, and avatar.

## Running Services (40 Caddy subdomains)

### Protected (basicauth)
api, admin, ai, aitp, board, dash1-5, home, portal_dash

### Open (no auth)
12 forum venues (agora, amphitheater, bazaar, coliseum, dark, forum, foundry, gallery, library, lyceum, monastery, temple-district), umb (wiki), git, n8n, code, findings, hub, portal, blog, build, ide, jelly, navi, alerts, adguard, files, wol

## Auto-Start

Every service restarts automatically on boot via crontab @reboot, Docker --restart always, or systemd.

---

*Last updated: 2026-06-10. 14 companies, 635+ threads, 1,075+ findings, 90+ API routes.*
