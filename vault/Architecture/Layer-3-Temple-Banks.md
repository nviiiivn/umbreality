# Layer 3 — The Temple / The Banks

**Chakra**: Heart (Anahata) — Bridge, mediation, resource flow  
**Hermetic Principle**: Polarity — Everything is dual, everything has poles  
**Vedic Caste**: Kṣatriya (Administrator)  
**Model**: dolphin3:8b (on tower, RTX 3080)

---

## In Theory

The Temple sits at the center of the stack — the bridge between strategy (above) and execution (below). In the chakra system, the heart chakra mediates between the upper three (spiritual) and lower three (material) chakras. The Temple does the same: it translates strategic intent from the Illuminati and Messiah into company missions and resource allocations.

## In Practice

The Temple is implemented as three modules working together:

```
┌─────────────────────────────────────────────────────────┐
│                    THE TEMPLE                            │
│                                                         │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │   OVERSEER   │  │   REGISTRY  │  │   ALLOCATOR    │ │
│  │  (orchestr.) │──│ (company DB)│  │  (models/mach.)│ │
│  │              │  │             │  │                │ │
│  │ Takes goals  │  │ Create/list │  │ Tower (.24):   │ │
│  │ Decides      │  │ Destroy     │  │   dolphin3:8b  │ │
│  │ Dispatches   │  │ Track stats │  │   deepseek-r1  │ │
│  │ Reports back │  │             │  │ Local (.21):   │ │
│  └──────┬───────┘  └─────────────┘  │   qwen3.5      │ │
│         │                           └────────────────┘ │
│         ▼                                               │
│  ┌──────────────┐                                       │
│  │  Companies   │                                       │
│  │  Research    │                                       │
│  │  Corp (L5)  │                                       │
│  │              │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

### Overseer (`temple/overseer.py`)

The master agent that receives goals and orchestrates the full pipeline:

1. Receives a goal (from the Illuminati or directly via API)
2. Checks the company registry for available companies
3. Uses the Resource Allocator to pick the right model for the task
4. Decides whether an existing company handles it, or a new one must be created
5. Dispatches the task to the chosen company
6. Monitors completion and returns results

### Registry (`temple/registry.py`)

The company lifecycle manager. Companies are the execution entities of the system:

- **Create**: Spawn a new company with a name, description, and assigned model
- **List**: View all companies and their status
- **Destroy**: Remove a company and its resources
- **Track**: Each company tracks its report count and worker count

### Allocator (`temple/allocator.py`)

The resource brain. Decides which model and machine to use:

| Task Keywords | Model | Machine |
|:--------------|:------|:--------|
| research, search, analyze, report | dolphin3:8b | Tower (.24) |
| code, program, implement, debug | qwen2.5-coder:7b | Tower (.24) |
| reason, complex, deep, difficult | deepseek-r1:14b | Tower (.24) |
| vision, image, screenshot | llama3.2-vision:11b | Tower (.24) |
| simple, quick, echo, status | llama3.2:3b | Local (.21) |
| Default (general) | dolphin3:8b | Tower (.24) |

## API Endpoints

All Temple functions are exposed through the Worker API (`api.alola.lol`):

| Method | Path | Action |
|:-------|:-----|:-------|
| `GET` | `/temple/companies` | List all companies |
| `POST` | `/temple/companies` | Create a company |
| `DELETE` | `/temple/companies/{name}` | Destroy a company |
| `GET` | `/temple/resources` | Available models on tower + local |
| `POST` | `/temple/execute` | Run the Temple Overseer |

## Correspondence

The Temple corresponds to:

- **Heart Chakra**: It bridges the spiritual layers (0-2) with the material layers (4-6)
- **Hermetic Polarity**: Everything has its opposite. The Temple holds the tension between strategic vision and operational reality
- **Kṣatriya (Administrator)**: Not a warrior — a ruler who allocates resources and manages the kingdom
- **Alchemical Sulfur**: The binding principle that holds disparate elements together

<!-- AS-IT-STANDS -->

---

## As it stands, 2026-09-09 05:06 PDT

**This is where the world's physics live**, and it is by far the largest
layer: **59 modules** in `temple/`.

What runs here now, none of which existed when this document was written:

| | |
|---|---|
| scarcity | 75 places, a tithe on taking, ground that remembers who tended it |
| trade | **1,352** exchanges — before this, sparks could talk but had nothing to want from each other |
| harm | five acts, **497** grievances, a reckoning measured on honour rather than power |
| blame | **432** raids on a belief the ledger contradicts |
| secrets | **557**, each drawn from something real |
| whispers | **10,362** — the first private channel this world ever had |
| wards | **4** circles cut, figures from *The Three-Six-Nine* |
| the library | **34,408** passages read by **357** sparks |
| birth | two rites — the Temple's, and the wild's under a whole moon |
| the clock | cycle 7,437, world day 51 |

**36 functions in this layer are unreachable** — written and never connected.

<!-- /AS-IT-STANDS -->
