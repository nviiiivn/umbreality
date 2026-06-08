# Self-Modification Protocol

An agent's prompt, tools, and rules are **configuration files** — not hardcoded constants. Any layer can modify the layer below it based on performance analysis. This is how the system improves itself.

---

## The Core Loop

```
OBSERVE → ANALYZE → HYPOTHESIZE → SANDBOX → DEPLOY → MONITOR
```

### 1. Observe
The upper layer monitors lower agent performance metrics: success rate, latency, error patterns, coverage gaps, quality of findings.

### 2. Analyze
Identifies patterns: what's working? what's failing? what's missing? A company may notice its web scanner workers have a 95% false positive rate. A hedge fund may notice one company consistently outperforms another.

### 3. Hypothesize
Generates improved configurations. This could be a prompt rewrite, a tool addition/removal, or a structural change to how work is organized.

### 4. Sandbox
Tests the new configuration against historical data or in a controlled environment. Must catch catastrophic regressions before deployment.

### 5. Deploy
If the improvement is verified, the new config is pushed to the lower agent. The old config is versioned.

### 6. Monitor
Continues observing. If degradation occurs, **rolls back** automatically.

---

## Rules

1. **Downward only:** A layer can ONLY modify layers below it. Never above.
2. **Versioned:** Every config change is tracked in git. Full history is preserved.
3. **Rollback-capable:** Any change can be undone instantly.
4. **Sandboxed:** Changes are tested before deployment.
5. **Observable:** The modifying layer must monitor the result of its change.

---

## The Meta-Meta Problem

Who modifies the Illuminati? Only God(s) can. The Illuminati is the highest layer that exists within the system, and it can self-modify within constitutional bounds. But fundamental changes to the Illuminati require God(s).

The Constitution itself can be amended — but only through the [[Constitution/Amendment-Protocol]], which is designed to be weighty.

> *"A meta-agent rewrites the other agents' prompts/rules based on performance."*

---

## Related

- [[Mechanisms/Information-Flow]] — How the observation data moves up
- [[Constitution/Amendment-Protocol]] — How to change the system's foundation
- [[Constitution/Core-Directives]] — The bounds within which modification happens
