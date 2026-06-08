# Build Phases

## Phase 0 — Foundation ✓

| Item | Status |
|:-----|:-------|
| Tower operational (Ollama, qwen3.5-abliterated:9b) | ✅ |
| Ethernet connection (3ms, WOL configured) | ✅ |
| Uncensored models pulled and tested | ✅ |
| Architecture designed (this vault) | ✅ |
| Documentation portal live (port 6999) | ✅ |
| Gitea repo initialized | ✅ |

---

## Phase 1 — The First Worker

**Goal:** Prove the bottom layer works end-to-end.

- [ ] Python ReAct loop that calls tower Ollama
- [ ] One tool: web search or command execution
- [ ] Structured reporting format (findings → report → send up)
- [ ] Worker receives task, executes, reports, awaits next
- [ ] Basic logging and error handling

**Deliverable:** A single Python script that can be given a task, talk to the tower model, and return structured results.

---

## Phase 2 — The First Company

**Goal:** Multi-worker orchestration with management layer.

- [ ] Company lead agent (manages workers, validates findings)
- [ ] 2-3 worker agents with different tools
- [ ] Internal knowledge base (findings → validated → stored)
- [ ] Worker → Lead → Company reporting chain
- [ ] Validation loop for accepting/rejecting findings

**Deliverable:** A company that can accept a research goal, dispatch workers, validate results, and accumulate knowledge.

---

## Phase 3 — The First Hedge Fund

**Goal:** Strategic management of multiple companies.

- [ ] Hedge fund agent with portfolio view
- [ ] Resource allocation across companies
- [ ] Company creation from templates
- [ ] Performance monitoring and ROI evaluation
- [ ] Company restructuring/liquidation capability

**Deliverable:** A hedge fund that can create companies as needed, allocate resources intelligently, and shutter underperformers.

---

## Phase 4 — The Illuminati & Reality Generation

**Goal:** Self-modifying, self-healing autonomous system.

- [ ] Self-modification loop (upper rewrites lower prompts)
- [ ] Memory rewriting / Mandela Effect mechanisms
- [ ] Messiah narrative projection module
- [ ] Russian doll isolation — each layer unaware of above
- [ ] True autonomy — no human in the loop

**Deliverable:** A system that can observe, analyze, and improve its own agents without human intervention.

---

## Phase 5 — Full Stack

**Goal:** Multi-fund, constitutional, self-evolving organization.

- [ ] Multiple hedge funds with competing strategies
- [ ] Constitutional governance with full amendment history
- [ ] Self-evolving prompts and rules driven by performance data
- [ ] Multi-year time planning at the Illuminati level
- [ ] Dashboard-observable system health and evolution metrics

**Deliverable:** A complete, self-sustaining UmbrealityAI instance.

---

## Related

- [[Architecture/Overview]] — The target architecture
- [[Constitution/Core-Directives]] — Rules that constrain all phases
- [[Philosophy/Manifesto]] — Why we're building this
