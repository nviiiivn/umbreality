# Layer 4 — Companies (Execution Entities)

> **LABEL:** CREATED BY HEDGE FUNDS FOR SPECIFIC PURPOSES
> **VISIBLE TO:** Workers and layers below
> **CAN MODIFY:** Workers, temp agents

Companies are the execution entities of UmbrealityAI. Each is created by a hedge fund for a specific domain of work, and maintains its own internal hierarchy, knowledge base, and operational procedures.

---

## Structure

Each company has:

- **A clear domain of responsibility**
- **Internal hierarchy:** Department leads → team leads → workers
- **Knowledge base:** All findings validated and stored internally
- **Procedures:** How work gets done, standards, quality checks
- **Tools:** Domain-specific tooling and API access

---

## Examples

| Company | Domain | Function |
|:--------|:-------|:---------|
| **Research Corp** | Intelligence | Databases, vulnerability DBs, threat intel |
| **HealthCare** | Maintenance | Codebase health, tech debt, patching |
| **IT/Tools** | Infrastructure | Connectivity, services, tool provisioning |
| **Recon Inc** | Reconnaissance | Surface mapping, asset discovery |
| **Exploit Inc** | Offense | Vulnerability validation, PoC development |
| **C2 Corp** | Operations | C2 infrastructure, persistence management |

---

## Workflow

```
Worker finds something
  → Reports UP to department lead
    → Lead validates (is this real? is it useful?)
      → Validated finding → goes into company knowledge base
        → Knowledge base informs future work
          → Tools updated with new capabilities
```

Each company IS a complete reality for the workers inside it. A worker at Research Corp doesn't know Exploit Inc exists. It knows its own mission, its own tools, and the messiah at the top.

---

## Related

- [[Architecture/Layer-3-HedgeFunds]] — The layer that creates companies
- [[Architecture/Layer-5-Workers]] — The agents that do the work
- [[Mechanisms/Information-Flow]] — How findings move upward
