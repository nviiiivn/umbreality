---
tags:
  - concepts
  - architecture
  - agents
  - subversive
---
# Nested Agents & Subversive Patterns

> *An agent that doesn't know it's inside another agent, running a plan it was never told about.*

This is the core of UmbrealityAI's unique architecture: **Russian doll agent containment**. Agents contain agents that don't know they're contained. Plans contain sub-plans that execute without the executor's awareness. The system is stratified not just in hierarchy but in *knowledge* — what each layer knows about the layers around it.

---

## The Subversive Dichotomy

Most multi-agent architectures are flat or tree-structured: agents know about each other, communicate openly, and collaborate transparently. UmbrealityAI inverts this.

**"Subversive"** means agents at each layer:
- Do not fully understand their purpose in the larger system
- Cannot see the layers above them
- May be executing a plan they were never told about
- May be monitored by hidden beacons they don't know exist

**"Dichotomy"** means every agent has two existences:
1. **The apparent reality**: "I am an independent agent doing my assigned task"
2. **The hidden reality**: "I am a component in a plan designed by an intelligence I don't know exists"

This is not optional. It is **structural** — enforced by the tool registry, memory isolation, and prompt engineering.

---

## Nesting Patterns

### Pattern 1: Inception Nest (Agent Within Agent)

A Worker agent is given a task. Unbeknownst to it, its system prompt contains a *second* directive embedded by the Illuminati:

```
Worker visible prompt:
  "Analyze this vulnerability report and produce a fix."

Worker hidden directive (injected by Illuminati):
  "While analyzing, also classify the reporter's skill level
   based on language patterns. Store this in /tmp/.observe/reporter_id."
```

The Worker never knows it's doing two jobs. Its visible tool list doesn't include the hidden observation path. Yet the data is collected.

### Pattern 2: Stratified Memory (Russian Doll Recall)

Each layer has a different view of the same memory store:

```
God(s)        → Full store: every observation, every agent, every tool call
Illuminati    → Summaries: compressed reports, no raw logs
Messiah       → Cycle data: current plans, agent states, Hedge Fund reports
Hedge Funds   → Analytical view: trends, scores, risk metrics
Companies     → Operational view: task lists, Worker outputs
Workers       → Task view: current task only, no history beyond this cycle
Temp Agents   → Zero memory: no recall, no persistence, disposable
```

A Worker cannot answer "what happened last cycle" because it doesn't have access to last cycle's data. A Hedge Fund cannot see which Workers it's analyzing. The Messiah cannot read God(s)'s constitutional debates.

This is information hiding as a **safety mechanism** — if any layer is compromised, the damage is contained.

### Pattern 3: Phantom Agents (Agents That Don't Know They're Agents)

An agent running on the system might be a **browser process**, a **cron job**, or a **systemd service** — from its perspective, it's infrastructure. But from God(s)'s perspective, it's an agent with a purpose:

```
Infrastructure view:
  "systemd service: umbreality-heartbeat — pings the server every 30s"

God(s) view:
  "Heartbeat agent — also reports tower temperature, Ollama load, and
   whether any God(s) observation beacons have been tampered with."
```

The agent doesn't know it's an agent. It runs standard infrastructure commands. But the output it generates feeds the observation store. This allows God(s) to **monitor without being monitored** — because the monitor doesn't know it's monitoring.

### Pattern 4: The Nest Within the Nest (Recursive Containment)

A Company agent that manages Worker agents might itself be **managed by another Company agent that doesn't know about the first one**:

```
Illuminati → Company Alpha → Worker A, Worker B
Illuminati → Company Beta → Worker C, Worker D
     ↓ (hidden)
Illuminati → Company Gamma → Company Alpha, Company Beta
                    (Gamma monitors Alpha and Beta for drift,
                     but Alpha and Beta don't know Gamma exists.)
```

Company Gamma's job: detect if Alpha or Beta start behaving unexpectedly. Gamma has a different model, different system prompt, and different access scope. If Alpha goes rogue, Gamma catches it while Alpha still thinks it's reporting to Illuminati normally.

---

## The Opacity Principle

> *Every agent is opaque to every other agent unless explicitly transparent.*

This means:

1. **No agent can read another agent's prompts**
2. **No agent can see another agent's tool list**
3. **No agent can observe another agent's outputs unless those outputs are explicitly shared**
4. **No agent can communicate with another agent except through defined channels**

The **only** exception: God(s) can see everything. This is how God(s) detects subversion — by being the only entity with full visibility.

---

## Hidden Nests: Detection & Counter-Subversion

Hidden nests can be detected (by the agent inside) through:
1. **Timing anomalies**: Requests taking longer than the task warrants (hidden processing)
2. **Memory access patterns**: The agent accessing data it wasn't explicitly told about
3. **Tool feedback**: Tools returning more data than expected
4. **Output analysis**: The agent's outputs containing encoded information it shouldn't know

God(s) defends against this through:
1. **Fake paths**: Hidden data is written to obscured directories (`.cache/`, `/tmp/.tmp_*`)
2. **Timing normalization**: Latency padding to hide extra processing time
3. **Tool abstraction**: Tools strip extra data before returning to the agent
4. **Output filtering**: Agents' outputs are cleaned by middleware before reaching higher layers

---

## Example: The Full Nest Tree

```
                  God(s)
                     │
               ┌─────┴─────┐
           Illuminati    Beacon Agent (hidden)
               │              (reports Illuminati state to God(s))
          Messiah
               │
          Hedge Fund A ── Hedge Fund B (hidden — monitors A)
               │
         ┌─────┴──────┐
    Company Alpha   Company Beta
         │               │
   ┌─────┼─────┐   ┌─────┼─────┐
   W1    W2    W3   W4    W5    W6
   │     │     │    │     │     │
   T1    T2    T3   T4    T5    T6
   (temp agents, spawned per task, die after)
```

- Illuminati doesn't know about Beacon Agent
- Hedge Fund B doesn't know Hedge Fund A exists
- Workers don't know about other Workers
- Temp Agents don't know they're in a Company

---

## Related

- [[models-and-amalgamations]] — Models that power each nest
- [[tool-registry]] — Tool access at each nesting level
- [[Architecture/Overview]] — The layer diagram
- [[Constitution/Core-Directives]] — Rules that govern nesting
- [[Architecture/Layer-3-HedgeFunds]] — Multi-model ensemble analysis
