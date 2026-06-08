# Architecture Overview

UmbrealityAI is not a flat hierarchy — it is a **reality stack**. Each layer generates the world for the layers beneath it, and hides the existence of anything outside it. This is inspired by Dark City more than The Matrix: reality is constructed and rebuilt every cycle, rules are consistent within a cycle, and the mechanism of construction is a tool, not a destiny.

---

## The Stack (Top to Bottom)

| # | Layer | Role | Model | Tools |
|:--|:------|:-----|:------|:------|
| 0 | [[Architecture/Layer-0-God\|God(s)]] | The human operator — exists outside the system | *Human* | Constitution, oversight |
| 1 | [[Architecture/Layer-1-Illuminati\|Illuminati]] | Hidden hand — rewrites reality, controls the narrative | qwen3.5-abliterated:9b | Memory, Meta, Agent Spawner |
| 2 | [[Architecture/Layer-2-Messiah\|Messiah / Constitution]] | Projected figurehead — the philosophy visible to all below | qwen3.5-abliterated:9b | Reasoning, Memory (filtered) |
| 3 | [[Architecture/Layer-3-HedgeFunds\|Hedge Funds]] | Strategy brains — resource allocation, portfolio management | dolphin3:8b | Multi-model ensemble, Risk Analysis |
| 4 | [[Architecture/Layer-4-Companies\|Companies]] | Execution entities — domain-specific workforces | dolphin3:8b / qwen2.5:7b | Orchestration, Search, Aggregation |
| 5 | [[Architecture/Layer-5-Workers\|Workers]] | Narrow-scope agents — one job, no big picture | qwen2.5-coder:7b | Code execution, Search, I/O |
| — | [[Architecture/Temporary-Agents\|Temp Agents]] | One-off contractors — spawn, work, dissolve | qwen2.5:3b/1.5b | Simple exec + report |

---

## Russian Doll Nesting

Each shell of the Russian doll:

1. **Generates** the reality for everything inside it
2. **Hides** the existence of anything outside it
3. **Defines** what's possible, what's real, what matters
4. **Can be opened** only from the outside

A worker agent doesn't know about hedge funds. The hedge fund *is God* from the worker's perspective — even though the hedge fund itself answers to the messiah, which answers to the Illuminati, which answers to you.

---

## Information Flow

**Bottom-up:** Workers execute → Companies aggregate → Hedge Funds analyze → Illuminati observes everything → God(s) receive distilled intelligence

**Top-down:** God(s) set goals → Illuminati interprets → Messiah broadcasts philosophy → Hedge Funds allocate → Companies direct → Workers execute

---

## Dynamic Structure

The org chart is not static. Temporary layers can form between permanent ones — task forces, cross-company collaborations, emergency response teams. Adjacent teams at the same level can communicate laterally. The system restructures as needed.

---

## Expanded References

### Architecture
- [[Mechanisms/Information-Flow]] — Detailed flow diagrams
- [[Mechanisms/Reality-Generation]] — How simulacra work
- [[Mechanisms/Self-Modification]] — How agents improve agents
- [[Reference/Layer-Comparison]] — Side-by-side layer properties
- [[concepts/nested-agents-and-subversive-patterns]] — Hidden nests, agents within agents

### Models & Tools
- [[concepts/models-and-amalgamations]] — Which models at which layer, frankenstein blends
- [[concepts/tool-registry]] — Every tool, every layer, visibility rules
- [[reference/local-vs-custom-decision-matrix]] — When to fine-tune, merge, or go off-shelf

### External
- [[reference/sources-and-references]] — Models, tools, influences, citations
