# Glossary of Terms

| Term | Definition |
|:-----|:-----------|
| **UmbrealityAI** | Umbrella + Reality. The umbrella of Russian doll systems generating the whole of our reality — a simulacrum allegory. |
| **God(s)** | The human operator(s) outside the system who set ultimate goals. Communicates only with the Illuminati. |
| **Illuminati** | The hidden layer that translates human intent into machine strategy and projects reality downward. Invisible to all layers below. Controls the Mandela Effect. |
| **Messiah / Constitution** | The projected figurehead visible to lower layers. A philosophy, not a brain. The written form is the Constitution. |
| **Hedge Fund** | A strategic agent that allocates resources and manages a portfolio of companies. The "real brains" of the operation. |
| **Company** | An execution entity created by a hedge fund for specific domain work. Has its own hierarchy, knowledge base, and tools. |
| **Worker** | A narrow-scope agent with one job and no visibility of the larger system. The bottom layer. |
| **Temp Agent / Contractor** | A one-off agent spawned for a specific task and dissolved when done. No memory between lifetimes. |
| **Mandela Effect** | The system's ability to retroactively rewrite its own history and memory. Executed by the Illuminati. |
| **Simulacrum** | A representation that replaces what it represents. The map becomes the territory. Each layer in UmbrealityAI is a simulacrum for the layer below. |
| **Russian Doll Reality** | The structural principle that each layer generates the universe for the layers within it — nesting, hidden exterior, generated reality. |
| **The Tuning** (Dark City) | The mechanism by which reality is reshaped. In UmbrealityAI, this is the Illuminati's reality generation capability. |
| **Epoch Boundary** | A major work cycle boundary where the Illuminati may reassess and rewrite reality (the Mandela Effect trigger point). |
| **Constitution** | The immutable core directives. Can be amended but only through a weighty process. |
| **Self-Modification** | The protocol by which upper layers rewrite lower agents' prompts, tools, and rules based on performance analysis. |
| **Bottom-Up Flow** | Information moving from workers upward through the hierarchy — raw findings → patterns → intelligence. |
| **Top-Down Flow** | Intent moving from God(s) downward through the hierarchy — raw goals → strategy → execution. |
| **Requisite Variety** | The principle that each layer receives only the resolution of information it can act on, not more. |
| **Reality Generation** | The mechanism by which each layer produces a complete, coherent reality for the layers within it. |


## New Terms (v2.0 — June 2026)

| Term | Definition |
|:-----|:-----------|
| **The Temple** | Layer 3 implementation — multi-company orchestration system with Overseer, Registry, and Allocator modules. Manages company lifecycle, resource allocation, and cross-company coordination. |
| **Overseer** | The Temple's master agent. Takes goals from the Illuminati, checks the company registry, allocates resources, dispatches to companies, and monitors completion. |
| **Registry** | The Temple's company lifecycle manager. Create, list, destroy companies dynamically. Each company has a name, description, status, and assigned model. |
| **Allocator** | The Temple's resource brain. Maps task types to optimal models and machines — research→dolphin3:8b on tower, code→qwen2.5-coder:7b, quick tasks→local llama3.2:3b. |
| **God's View** | `admin.alola.lol` — The admin panel. Live system status, command console, Illuminati interface, activity feed, knowledge browser, temple management. The human's window into the system. |
| **Illuminati Interpreter** | `POST /illuminate` — The Layer 1 endpoint that translates natural language intent into structured system commands. Takes "what are my agents doing" and returns `{"layer": 3, "action": "monitor", ...}`. |
| **LAI Bridge** | `lai` CLI tool — Local AI Bridge. Calls the tower Ollama from the command line. `lai --role coder "write a function"` invokes dolphin3:8b directly. Saves OpenCode credits for routine tasks. |
| **Activity Feed** | In-memory ring buffer tracking every system action. Accessible via `GET /activity`. Used by the God's View for real-time monitoring. |
| **Knowledge Base** | SQLite store for company findings and reports. Each finding has: task, worker, content, source, confidence, validation status. Accessible via `GET /company/knowledge`. |
| **dolphin3:8b** | Primary model for Layers 1 and 3. Uncensored, runs on tower RTX 3080. Used for intent interpretation and company orchestration. |
| **Tower** | `192.168.86.24` — x86_64 machine with RTX 3080 20GB running Ollama with 58 models. Primary inference engine for all Umbreality agents. |
| **ai-tp** | `192.168.86.21` — Raspberry Pi 5 running Caddy, Cloudflare tunnel, Worker API, Temple, all web services. The orchestration node. |
| **Phase 1** | First Worker — Python ReAct loop with web search + command execution tools. `POST /execute` |
| **Phase 2** | Research Corp — Multi-worker company with lead agent, knowledge base, and reporting chain. `POST /company/execute` |
| **Phase 3** | The Temple — Multi-company orchestration with Overseer, Registry, Allocator. `POST /temple/execute` |
