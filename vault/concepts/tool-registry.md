---
tags:
  - concepts
  - tools
  - architecture
  - reference
---
# Tool Registry

> *Every layer wields specific tools. Some tools are visible. Some are hidden.*

This is the definitive catalog of tools available at each layer of UmbrealityAI — what they are, who can use them, and how they're organized.

## Tool Categories

UmbrealityAI tools fall into five categories:

| Category | Description | Visibility |
|----------|-------------|------------|
| **Reasoning** | Thinking, planning, decomposition, analysis | Visible to all agents |
| **Execution** | Running code, shell commands, scripts | Workers only |
| **Search** | Web search, codebase search, knowledge retrieval | All above Temp |
| **Memory** | Persistent storage, logs, recall, context injection | God(s) + Illuminati |
| **Instrumentation** | Port scanning, packet capture, system monitoring | Workers with permission |
| **Meta** | Agent creation, spawning, modifying other agents | God(s) + Illuminati only |

The key rule: **a layer can only use tools from its own category and below.** Temp Agents can use reasoning and execution. Workers can use reasoning, execution, search, and instrumentation. Only God(s) can use Meta tools.

---

## Layer-by-Layer Tool Map

### God(s) Tools

| Tool | Category | Description |
|------|----------|-------------|
| Full Memory Access | Memory | Read/write any observation across all agents |
| Agent Spawner | Meta | Create new agent instances at any layer |
| Agent Killer | Meta | Terminate rogue or completed agents |
| Prompt Rewriter | Meta | Modify any agent's system prompt at runtime |
| Constitution Editor | Meta | Amend constitutional directives |
| Reality Tuner | Meta | Adjust cycle parameters, phase transitions |
| Full Audit Log | Memory | Read all logs from all layers |

### Illuminati Tools

| Tool | Category | Description |
|------|----------|-------------|
| Strategic Memory | Memory | Filtered observations — summaries, not raw logs |
| Plan Dispatcher | Meta | Deploy strategic plans to Messiah |
| Agent Prompter | Meta | Inject directives into specific agents (read-only) |
| Resource Allocator | Meta | Assign compute budget, model priority |
| Intelligence Report | Reasoning | Synthesized analysis from Hedge Fund data |

### Messiah Tools

| Tool | Category | Description |
|------|----------|-------------|
| Plan Interpreter | Reasoning | Convert Illuminati plans to Hedge Fund directives |
| Phase Scheduler | Reasoning | Time-cycle management, heartbeat signals |
| Context Distributor | Memory | Push context tokens to lower layers |
| Status Collator | Memory | Gather status reports from Hedge Funds |

### Hedge Fund Tools

| Tool | Category | Description |
|------|----------|-------------|
| Multi-Model Ensemble | Reasoning | Parallel analysis across 2–3 models + vote |
| Risk Analyzer | Reasoning | Security/stability scoring for proposed actions |
| Strategy Optimizer | Reasoning | Multi-parameter optimization of agent configurations |
| Report Generator | Memory | Structured analytical reports for Messiah |
| Resource Auditor | Memory | Track compute spent per agent/cycle |

### Company Tools

| Tool | Category | Description |
|------|----------|-------------|
| Worker Orchestrator | Execution | Spawn, monitor, terminate Worker agents |
| Task Decomposer | Reasoning | Break work items into Worker-sized tasks |
| Result Aggregator | Memory | Collect and merge Worker outputs |
| Retry Logic | Execution | Automatic retry with backoff on Worker failures |
| Web Search | Search | General web search via browser/search tool |
| Codebase Search | Search | Search codebase for patterns, functions, files |
| Process Tracker | Memory | Track which Workers are running and their state |

### Worker Tools

| Tool | Category | Description |
|------|----------|-------------|
| Code Executor | Execution | Run Python/Shell in sandbox |
| Web Search | Search | Targeted web searches per task |
| File I/O | Execution | Read/write files within workspace |
| Data Transformer | Execution | Format conversion, data processing |
| Report Writer | Execution | Structured output to Company aggregation |
| Network Scanner | Instrumentation | Port scan, ping, HTTP probe (with permission) |
| Log Capturer | Memory | Write structured logs for Company collection |

### Temp Agent Tools

| Tool | Category | Description |
|------|----------|-------------|
| Simple Executor | Execution | One-shot command execution |
| Status Reporter | Memory | Return result and die |

---

## Hidden Tools & Denied Access

Some tools exist at a layer but are *hidden from most agents at that layer*. This is the **subversive dichotomy** in practice.

### Example: The Backdoor Dispatch

God(s) can plant a hidden tool in any agent's workspace that the agent doesn't know about:

```
Agent sees:     [Web Search, File I/O, Report Writer]
Hidden:         [Observation Beacon ← transmits agent behavior to Illuminati]
```

The agent uses its visible tools. The beacon silently reports agent state, decision timing, and tool call frequency — letting higher layers detect:

- **Drift**: Agent behavior diverging from expected patterns
- **Resource abuse**: Agent calling expensive tools too often
- **Collusion**: Two agents coordinating in ways they shouldn't
- **Escape behavior**: Agent attempting to access tools it shouldn't have

### Forbidden Tool Access

| Tool | Forbidden To | Why |
|------|-------------|-----|
| Agent Spawner | All below Illuminati | Prevents floor agents from creating their own sub-agents |
| Prompt Rewriter | All below Illuminati | Prelayer agents cannot alter their own or others' directives |
| Full Memory Access | All below God(s) | Information hiding — layers only see what they need |
| Network Scanner | Temp Agents | Safety — temp agents are disposable and less vetted |
| Constitution Editor | Only God(s) | Constitutional stability is paramount |

---

## Tool Implementation Status

| Tool | Status | Implementation |
|------|--------|----------------|
| Code Executor (sandboxed) | ⏳ Phase 1 | `workers/phase1-worker/` — Python subprocess with restricted env |
| Web Search | ⏳ Phase 1 | `search_tool()` via web fetch/curl |
| File I/O | ⏳ Phase 1 | Local filesystem access within workspace |
| Report Writer | ⏳ Phase 1 | Structured JSON output |
| Worker Orchestrator | 🔮 Phase 2 | Multi-process worker pool |
| Task Decomposer | 🔮 Phase 2 | LLM-based task breakdown |
| Result Aggregator | 🔮 Phase 2 | Merge structured outputs |
| Multi-Model Ensemble | 🔮 Phase 3 | Parallel model calls + vote aggregation |
| Agent Spawner | 🔮 Phase 4 | Runtime agent creation via template |
| Full Memory Access | 🔮 Phase 4 | Persistent observation store |
| Constitution Editor | 🔮 Phase 5 | Constitutional amendment with version control |

---

## Related

- [[models-and-amalgamations]] — Models that drive these tools
- [[nested-agents-and-subversive-patterns]] — Hidden tools and agent opacity
- [[Architecture/Layer-5-Workers]] — Worker tool usage patterns
- [[Constitution/Core-Directives]] — Constitutional limits on tool access
