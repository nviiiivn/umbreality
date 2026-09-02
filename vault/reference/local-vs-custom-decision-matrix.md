---
tags:
  - reference
  - models
  - architecture
  - decision
---
# Local vs Custom: Decision Matrix

> *When do we use an off-the-shelf model, a custom system prompt, a fine-tune, a model merge, or a from-scratch train?*

Every decision point in UmbrealityAI requires a choice: use an existing model as-is, customize it lightly, or build something new. This page documents the decision framework and the specific decisions made for each component.

---

## The Decision Framework

### Question 1: Does an existing model already do this well enough?

| If… | Then… |
|-----|-------|
| General reasoning / chat / analysis | Off-shelf + system prompt |
| Code generation | Off-shelf coder variant + system prompt |
| Structured classification (fixed categories) | Off-shelf + few-shot examples in prompt |
| Recurring fixed-format output | Fine-tune (saves tokens and reduces latency) |
| Niche domain with no good base model | Fine-tune or train from scratch |

### Question 2: What's the failure cost?

| Cost Level | Examples | Approach |
|------------|----------|----------|
| Low | Temp agents, trivial formatting, health checks | Off-shelf smallest model |
| Medium | Worker analysis, report writing | Off-shelf + system prompt + critic loop |
| High | Security decisions, fund allocation, constitutional judgments | Ensemble (2+ models) + judge |
| Critical | God(s) meta-decisions, agent spawning authorization | Ensemble + human-in-the-loop |

### Question 3: How often does this run?

| Frequency | Approach |
|-----------|----------|
| Once per cycle or less | Full model, maximum quality — latency irrelevant |
| Tens per cycle | Balanced model, system prompt optimization |
| Hundreds per cycle | Small model, fine-tuned for task |
| Thousands per cycle | Tiny model (3B or less), CPU-friendly quantization |

---

## The Matrix

| Component | Model | Approach | Rationale |
|-----------|-------|----------|-----------|
| God(s) reasoning | huihui_ai/qwen3.5-abliterated:9b | Off-shelf + system prompt | General reasoning is a solved problem. Prompt engineering handles persona separation. |
| Illuminati planning | huihui_ai/qwen3.5-abliterated:9b | Off-shelf + system prompt + memory filter | Same model as God(s) but different information diet creates emergent behavior. |
| Messiah cycle management | huihui_ai/qwen3.5-abliterated:9b | Off-shelf + system prompt | Time-scoped context window handles cycle boundaries. |
| Hedge Fund analysis | dolphin3:8b | Off-shelf + system prompt | Dolphin's DeepSeek lineage gives different reasoning style — ensemble diversity. |
| Company orchestration | dolphin3:8b / qwen3.5:7b | Off-shelf + system prompt + Worker templates | Orchestration logic is prompt-driven; no retraining needed. |
| Code generation | qwen2.5-coder:7b | Off-shelf + system prompt | Coder variant is purpose-built; fine-tuning would add marginal value. |
| Vulnerability scanning | qwen2.5-coder:7b | ⏳ **Planned fine-tune** | Structured CVE classification benefits from domain-specific training data. |
| Security policy checks | qwen3.5:7b | ⏳ **Planned fine-tune** | Recurring classification task with fixed output schema. |
| Constitution interpretation | qwen3.5-abliterated:9b | Off-shelf + system prompt | Constitutional reasoning requires full context window and uncensored thinking. |
| Temp Agent responses | qwen2.5:3b / 1.5b | Off-shelf | Disposable — any consistency is wasted optimization. |
| Tool selection routing | qwen2.5:7b | Off-shelf + system prompt | General classification task. |
| Observation synthesis | huihui_ai/qwen3.5-abliterated:9b | Off-shelf + system prompt | Requires full context window to synthesize across many observations. |

---

## When to Fine-Tune

Fine-tuning (via QLoRA on RTX 3080) becomes worthwhile when:

1. **Task frequency is high** (>100 invocations per day)
2. **Output format is rigid** (JSON schema, classification labels)
3. **Latency matters** (fine-tuned model doesn't need few-shot examples in prompt)
4. **The off-shelf model consistently makes predictable errors**

### Current Fine-Tune Candidates

| Candidate | Training Data | Expected Improvement |
|-----------|-------------|---------------------|
| Security Auditor | CVE database, vulnerability reports, patch diffs | Better zero-shot CVE classification, fewer false positives |
| Constitution Keeper | Past constitutional edge cases, rulings | Consistent policy interpretation |
| Tool Router | Tool call traces, successful vs failed routing | Fewer tool mis-selections, faster routing |

### QLoRA on RTX 3080 20GB

| Parameter | Value |
|-----------|-------|
| Base model max | 9B (qwen3.5) at Q4_K_M |
| Rank | 16–64 |
| LoRA alpha | 32–128 |
| Target modules | q_proj, v_proj (standard QLoRA) |
| Dataset size | 500–5000 examples ideal |
| Training time | 2–8 hours per fine-tune |
| VRAM peak | ~7GB during training (leaves 1GB for system) |

---

## When to Model Merge (Frankenstein)

Model merging combines weights from two or more models without training. Useful when:

1. **Two models have complementary strengths** (e.g., code + reasoning)
2. **No suitable single model exists** for the task
3. **You want to combine uncensored behavior with instruction following**

### Merge Techniques Available

| Technique | Description | Example Use |
|-----------|-------------|-------------|
| Linear (weighted average) | `merged = α·A + (1-α)·B` | General capability blend |
| SLERP | Spherical interpolation — preserves model geometry | Merging models of different sizes |
| TIES | Trim, Elect Sign, Merge — resolves sign conflicts | Combining fine-tuned weights with base |
| DARE | Drop And REscale — sparsifies delta weights before merging | Preserving base capabilities while adding specialist skills |

### Planned Merges

| Merge | Components | Goal |
|-------|------------|------|
| Code Reasoner | qwen2.5-coder:7b + qwen3.5:7b | Agent that can reason about architecture while writing code |
| Unfiltered Analyst | dolphin3:8b + qwen3.5-abliterated:9b | DeepSeek reasoning + Qwen uncensored knowledge base |
| Lightweight Thinker | qwen2.5:3b + small reasoning blend | A tiny model that punches above its weight for Temp Agent tier |

---

## When to Train From Scratch

**Almost never**, with one exception:

| Scenario | Why From Scratch | Alternative |
|----------|-----------------|-------------|
| Custom embedding model | Fine-tuned embeddings from Sentence Transformers need domain-specific training data | Use off-shelf if not mission-critical |
| Tiny domain model (<1B) | A 500M–1B model trained on security research corpus could outperform general 7B | Start with continued pre-training of existing small model |
| Novel architecture experiment | Research exploration of new agent architectures | Keep in sandbox, not production |

---

## Current Layer Decisions Summary

```
Layer            Model               Approach        Why Not Custom?
─────            ─────               ────────        ───────────────
God(s)           qwen3.5-ab:9b       off-shelf       No model better at this size
Illuminati       qwen3.5-ab:9b       off-shelf       Same brain, different info diet
Messiah          qwen3.5-ab:9b       off-shelf       Same
Hedge Funds      dolphin3:8b         off-shelf       Ensemble diversity, no fine-tune needed
Companies        dolphin3:8b         off-shelf       Orchestration is prompt-driven
Workers          qwen2.5-coder:7b    off-shelf       Coder variant solves code tasks
Temp Agents      qwen2.5:3b/1.5b    off-shelf       Disposable; don't invest in ephemeral
Security Auditor qwen2.5-coder:7b    ⏳ fine-tune    Structured CVE work benefits from spec
Constitution     qwen3.5-ab:9b       off-shelf       Reasoning task, not classification
```

**The rule**: default to off-shelf + system prompt. Fine-tune only when data + frequency justify it. Merge when models are complementary. Train from scratch almost never.

---

## Related

- [[models-and-amalgamations]] — Full model catalog
- [[tool-registry]] — Tools at each layer
- [[Architecture/Overview]] — Architectural context for model decisions
