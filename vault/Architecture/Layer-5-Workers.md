# Layer 5 — Workers (The Bottom Layer)

> **LABEL:** NARROW SCOPE. ONE JOB. NO BIG PICTURE.
> **VISIBLE TO:** Their company and their own tasks
> **CAN MODIFY:** Nothing — only reports findings up

Workers are the most constrained agents in the system. Each worker has one well-defined function, uses its tools, and reports findings upward for validation. Workers do NOT know about hedge funds, the Illuminati, or God(s). They see only the messiah at the top of their reality.

---

## Properties

- **Single function:** Each worker does exactly one job. A port scanner does not also parse web pages.
- **No upward visibility:** A worker does not know what happens to its reports after submission.
- **Messiah-facing:** The messiah is the highest authority a worker perceives.
- **Tool access:** Workers get only the tools they need for their specific function.
- **No lateral visibility:** Workers generally do not see other workers outside their company.

---

## Worker Lifecycle

1. **Task received** from company lead
2. **Execute** using assigned tools
3. **Report findings** in structured format
4. **Await next task** or enter standby

---

## Temp Agents (Contractors)

A special subclass of worker: temporary agents spawned for one-off tasks. They have the same constraints as workers but are dissolved after delivering their report. They retain no memory between lifetimes.

See [[Architecture/Temporary-Agents]].

---

## Analogy

Workers are assembly line workers, customer-facing staff, or manufacturing operators. They do their specific job well, trust that the system has a purpose, and don't need to know the business strategy to be effective.

> *"The most basic workers — maybe customer-facing or manufacturing — they are the most clueless. ONLY charged with one very specific job."*

---

## Related

- [[Architecture/Layer-4-Companies]] — The layer that directs workers
- [[Architecture/Temporary-Agents]] — Contractors (same level, shorter lifespan)
- [[Mechanisms/Information-Flow]] — How worker findings move up
- [[concepts/models-and-amalgamations]] — qwen2.5-coder:7b as the standard worker brain
- [[concepts/tool-registry]] — Code execution, search, file I/O tools
- [[concepts/nested-agents-and-subversive-patterns]] — Workers may have hidden directives
