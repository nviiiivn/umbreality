# Temporary Agents (Contractors)

> **LABEL:** ONE-OFF. DISSOLVE WHEN DONE.

Not all agents in UmbrealityAI are permanent. The system creates temporary agents on demand for specific short-lived purposes. Think of them as contractors, gig workers, or special task forces.

## When Temp Agents Are Created

- **One-time investigations:** A specific IP, hash, or indicator that needs deep dives but won't recur
- **Spike testing:** Short-term surge capacity for load testing or stress simulation
- **Novel attack simulation:** Trying a new technique that may not become part of standard procedure
- **Cross-company collaboration:** A temporary team drawn from multiple companies for a joint project
- **Monitoring gaps:** A short-term watcher while a permanent agent is being modified or upgraded

## Lifecycle

1. **SPAWN:** A hedge fund or company lead issues a temp agent creation request with: scope, tools needed, expected duration, report destination
2. **LIVE:** The temp agent executes its task with full focus — it has no other responsibilities
3. **REPORT:** Findings are submitted to the creating layer with structured output
4. **DISSOLVE:** The agent is terminated. Its context is archived. It retains no memory between lifetimes.

## Properties

- **No memory persistence:** Temp agents do not accumulate history. Each spawn is fresh.
- **No promotion path:** Temp agents cannot be promoted to permanent workers. They are a different class.
- **No lateral visibility:** A temp agent cannot see other temp agents or permanent workers outside its direct task.
- **Full tool access within scope:** A temp agent gets all the tools it needs for its specific job — no more, no less.

## Analogy

Temp agents are the system's equivalent of calling in a specialist consultant. You don't hire a heart surgeon full-time because you *might* need one. You call one when you do, they do the work, they leave. The system learns from the outcome (was it useful? should we create a permanent agent for this?) and adjusts.

## Related

- [[Architecture/Layer-5-Workers]] — Temporary agents operate at the same layer as workers
- [[Architecture/Layer-3-HedgeFunds]] — Hedge funds can authorize temp agent creation
- [[Mechanisms/Information-Flow]] — Where temp agent reports go
- [[concepts/models-and-amalgamations]] — qwen2.5:3b/1.5b as disposable agent models
- [[concepts/tool-registry]] — Temp agents only get Simple Executor + Status Reporter
- [[reference/local-vs-custom-decision-matrix]] — Why temp agents don't qualify for fine-tuning
