---
tags:
  - concepts
  - models
  - architecture
  - amalgamation
---
# Models & Amalgamations

> *Which model goes where, why, and when do we stitch them together?*

Every layer of UmbrealityAI runs on **local uncensored models** via Ollama on the tower (RTX 3070 8GB). This page maps specific models to layers, explains the reasoning, and documents the art of *model amalgamation* — blending multiple models to create hybrid intelligences.

## The Constraint

| Resource | Spec |
|----------|------|
| GPU | RTX 3070, 8GB VRAM |
| CPU | Ryzen 5 5600X, 32GB RAM |
| Backend | Ollama on CachyOS |
| Max quant | Q4_K_M fits at 8B, Q3_K_S at 14B |
| Context limit | 32K–100K depending on model |

This means **no 70B models**, no massive MoE in full precision. The art is in fitting the *right* model to the *right* role.

---

## Layer-to-Model Map

```
LAYER                     MODEL                              WHY
─────                     ─────                              ───
God(s)           huihui_ai/qwen3.5-abliterated:9b    biggest brain that fits 8GB
Illuminati       huihui_ai/qwen3.5-abliterated:9b    same — shared "high reason" pool
Messiah          huihui_ai/qwen3.5-abliterated:9b    same model, different system prompt
Hedge Funds      dolphin3:8b / qwen3.5:7b            faster, specialized analysis
Companies        dolphin3:8b / qwen2.5:7b            throughput-optimized for multiple agents
Workers          qwen2.5-coder:7b / qwen3.5:7b       code/tool-call focused
Temp Agents      qwen2.5:3b / qwen2.5:1.5b           ultra-fast, disposable, high volume
```

### Primary Model: `huihui_ai/qwen3.5-abliterated:9b`

This is the **brain** of the system — God(s), Illuminati, and Messiah all use it.

**Why this model:**
| Factor | Value |
|--------|-------|
| Parameters | 9B (Qwen 3.5 base) |
| Context | 131,072 tokens |
| Tool use | Native function-calling via Qwen's format |
| Vision | Supports vision inputs |
| Speed on 3070 | ~40–60 t/s at Q4_K_M |
| Uncensored | Abliterated — guardrails surgically removed |
| Thinking | Supports chain-of-thought reasoning (extended thinking mode) |

**Dual-persona trick:** God(s), Illuminati, and Messiah are all *the same model with different system prompts and memory scopes*. This is intentional:
- **God(s)** sees the full persistent memory store
- **Illuminati** sees filtered strategic memory (no raw worker logs)
- **Messiah** sees only the current cycle and Hedge Fund reports

Same neural substrate, different information diets. Like one brain with multiple personalities that don't know each other exist.

### Secondary Model: `dolphin3:8b`

Used for Hedge Funds, Companies, and analysis-heavy Workers.

**Why:**
| Factor | Value |
|--------|-------|
| Base | DeepSeek-derived architecture |
| Uncensored | Dolphin fine-tune — guardrails removed |
| Tool use | Good function-calling support |
| Speed | ~50–70 t/s |
| Trading | Different reasoning style from Qwen — ensemble diversity |

Dolphin's different training lineage means it *thinks differently* than Qwen. This is valuable for:
- Cross-verification: two models analyzing the same problem
- Ensemble voting in Hedge Fund strategic decisions
- Avoiding single-model blind spots

### Worker Models: `qwen2.5-coder:7b` and `qwen2.5:7b`

Code-generation and tool-calling workers use the coder variant. General-purpose workers use the base.

| Variant | Best For | Speed |
|---------|----------|-------|
| qwen2.5-coder:7b | Code generation, tool orchestration, pipeline scripts | ~50 t/s |
| qwen2.5:7b | Data analysis, report writing, web research | ~55 t/s |

### Temp Agents: `qwen2.5:3b` and `qwen2.5:1.5b`

Disposable agents that run one task then die. These are:
- **Cheap**: run on CPU if GPU saturated — takes 1–3 seconds per response
- **Disposable**: no persistent state, no memory, no identity
- **Stateless**: each call is self-contained, results are logged externally

---

## Model Amalgamations (Frankensteining)

> *When one model isn't enough, stitch two together.*

### Pattern 1: Thinker + Writer

A **heavy thinker** (qwen3.5-abliterated:9b) reasons about the problem, produces structured analysis. Then a **fast writer** (dolphin3:8b or qwen2.5-coder:7b) transforms that analysis into the final output.

```
Problem → God(s) [thinks] → raw analysis → Worker [writes] → polished output
```

Used when: output formatting, code generation, or report writing would waste the thinker's context window.

### Pattern 2: Ensemble Voting

Three different models each produce an independent answer, then a judge model (God(s)) selects or synthesizes.

```
         ┌→ dolphin3:8b ──┐
Problem ─┼→ qwen3.5:7b ──┼→ Judge (qwen3.5-a) → final decision
         └→ qwen2.5:7b ──┘
```

Used when: security decisions, resource allocation, any high-stakes binary judgment.

### Pattern 3: Critic Loop

Worker produces output → Critic model analyzes for flaws → Worker revises. Repeat until Critic passes.

```
Worker ──→ output ──→ Critic (dolphin3) ──→ pass? ──→ done
                       ↑                        │ fail
                       └── revision request ────┘
```

Used when: code quality, security policy generation, constitutional interpretation.

### Pattern 4: Fine-Tuned Specialists

For recurring tasks, a base model is fine-tuned on the task and swapped in as a drop-in replacement.

| Specialist | Base | Task | Status |
|------------|------|------|--------|
| Security Auditor | qwen2.5-coder:7b | Vulnerability scanning | Planned |
| Constitution Keeper | qwen3.5:7b | Policy violation detection | Planned |
| Reality Tuner | qwen3.5-abliterated | Cycle/phase transitions | Research |

---

## Local vs Custom vs Fine-Tuned vs Ensemble

| Approach | When to Use | Examples |
|----------|-------------|---------|
| **Off-shelf local** | General reasoning, tool use, anything a standard LLM can do | God(s), Illuminati, basic Workers |
| **Custom system prompt** | Most agents — different role/persona without retraining | Messiah, Hedge Funds, Companies |
| **Fine-tuned (LoRA/QLoRA)** | Recurring structured task with a fixed format | Security Auditor, Constitution Keeper |
| **Model merge (frankenstein)** | When two models have complementary strengths | Thinker+Writer chains |
| **Ensemble (multi-model)** | High-stakes decisions needing diversity | Security checks, fund allocations |
| **Disposable tiny model** | Trivial, stateless, high-volume tasks | Temp Agents, health checks |

---

## Running Multiple Models on 8GB VRAM

RTX 3070 8GB cannot load two 8B Q4 models simultaneously. Strategy:

1. **Shared pool**: One model loaded at a time per priority queue
2. **CPU offload**: Small models (3B/1.5B) run on CPU or partial GPU
3. **Context eviction**: Save/restore KV cache for round-robin
4. **Ollama keep_alive**: Tuned per model — thinkers stay hot, temps evict immediately

```
Priority:
  God(s)         → keep_alive: 5m  (hot, infrequent but critical)
  Illuminati     → keep_alive: 5m  (hot)
  Hedge Fund     → keep_alive: 2m  (warm)
  Worker         → keep_alive: 30s (cold, loaded on demand)
  Temp Agent     → keep_alive: 0   (load, run, evict)
```

---

## Related

- [[tool-registry]] — Tools at each layer
- [[nested-agents-and-subversive-patterns]] — How agents contain agents
- [[Architecture/Layer-3-HedgeFunds]] — Strategic analysis with multi-model ensembles
- [[Architecture/Layer-5-Workers]] — Tool-using agents at scale
