---
tags:
  - reference
  - external
  - links
  - bibliography
---
# Sources & References

> *Models, tools, projects, and influences referenced throughout the UmbrealityAI vault.*

---

## Models

### Primary Models

| Model | Link | Notes |
|-------|------|-------|
| huihui_ai/qwen3.5-abliterated:9b | [Ollama](https://ollama.com/huihui_ai/qwen3.5-abliterated) | Abliterated Qwen 3.5 — no guardrails, 131K context, vision+tool use |
| Qwen 3.5 (base) | [Hugging Face](https://huggingface.co/Qwen/Qwen3.5-9B) | Alibaba's latest, strong reasoning + tool use |
| dolphin3:8b | [Ollama](https://ollama.com/dolphin3:8b) | DeepSeek-based, uncensored, GuardrailRIP variant |
| qwen2.5:7b | [Ollama](https://ollama.com/qwen2.5:7b) | Previous gen, well-rounded general purpose |
| qwen2.5-coder:7b | [Ollama](https://ollama.com/qwen2.5-coder:7b) | Code-specialized, strong tool calling |
| qwen2.5:3b | [Ollama](https://ollama.com/qwen2.5:3b) | Lightweight, CPU-friendly |
| qwen2.5:1.5b | [Ollama](https://ollama.com/qwen2.5:1.5b) | Ultra-light, disposable agent use |

### Model Techniques

| Technique | Link | Description |
|-----------|------|-------------|
| Abliteration | [failspy/abliterator](https://huggingface.co/failspy/abliterator) | Automated removal of refusal/disalignment vectors from models |
| QLoRA | [Hugging Face PEFT](https://huggingface.co/docs/peft/en/developer_guides/quantization) | 4-bit quantized fine-tuning — fine-tune 9B on 8GB VRAM |
| TIES-Merging | [Arxiv: 2306.01708](https://arxiv.org/abs/2306.01708) | Trim, Elect Sign, Merge — resolves weight conflicts in model merging |
| SLERP | [Wikipedia](https://en.wikipedia.org/wiki/Slerp) | Spherical linear interpolation for smooth model weight blending |
| DARE | [Arxiv: 2311.03099](https://arxiv.org/abs/2311.03099) | Drop And REscale — sparsifies delta weights before merging |

---

## Tools & Infrastructure

### Core Stack

| Tool | Link | Use in uAI |
|------|------|------------|
| Ollama | [ollama.com](https://ollama.com) | Local model serving (Ollama API) |
| MkDocs | [mkdocs.org](https://www.mkdocs.org) | Documentation portal framework |
| Material for MkDocs | [squidfunk.github.io](https://squidfunk.github.io/mkdocs-material/) | Theme, mobile-responsive, rich UI |
| Gitea | [gitea.io](https://about.gitea.com) | Self-hosted git (192.168.86.21:3100) |
| systemd | [freedesktop.org](https://systemd.io) | Service management for persistent processes |
| Python 3.11 | [python.org](https://python.org) | Agent runtime (Phase 1 worker) |
| Obsidian | [obsidian.md](https://obsidian.md) | Vault development environment |

### Network & Tunneling

| Tool | Link | Use in uAI |
|------|------|------------|
| serveo.net | [serveo.net](https://serveo.net) | Public HTTP tunnel (port 6999 → docs portal) |
| SSH | OpenSSH | Tunnel transport layer |
| Gunicorn | [gunicorn.org](https://gunicorn.org) | WSGI server (future dashboard use) |

### Security & Monitoring

| Tool | Link | Use in uAI |
|------|------|------------|
| fail2ban | [github.com/fail2ban](https://github.com/fail2ban/fail2ban) | Brute-force protection on exposed services |
| GNU Screen / tmux | [tmux.github.io](https://github.com/tmux/tmux) | Persistent agent sessions |
| netstat / ss | iproute2 | Port monitoring agent instrumentation |
| curl / wget | curl.se | Web search primitive |

---

## Influences & Related Projects

### Multi-Agent Systems

| Project | Link | Influence on uAI |
|---------|------|-----------------|
| AutoGPT | [github.com/Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | Early inspiration for autonomous goal-driven agents |
| BabyAGI | [github.com/yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi) | Task-driven autonomous agent pattern |
| Microsoft AutoGen | [github.com/microsoft/autogen](https://github.com/microsoft/autogen) | Multi-agent conversation framework |
| LangChain | [langchain.com](https://langchain.com) | Tool-use and agent chaining patterns (though uAI avoids its complexity) |
| LangGraph | [langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/) | Graph-based agent orchestration ideas |
| CrewAI | [crewai.com](https://github.com/joaomdmoura/crewai) | Role-based agent collaboration patterns |
| MetaGPT | [github.com/geekan/metagpt](https://github.com/geekan/metagpt) | Software company simulation with SOP-driven agents |
| CAMEL | [github.com/camel-ai/camel](https://github.com/camel-ai/camel) | Role-playing agent communication framework |
| OpenDevin | [github.com/OpenDevin/OpenDevin](https://github.com/OpenDevin/OpenDevin) | AI software development agent |
| smol.ai / smolagents | [huggingface.co/smolagents](https://huggingface.co/docs/smolagents) | Lightweight HuggingFace agent framework, code-action agents |

### Security & Red Teaming

| Project | Link | Influence on uAI |
|---------|------|-----------------|
| OWASP Top 10 | [owasp.org](https://owasp.org/www-project-top-ten/) | Vulnerability classification standard |
| MITRE ATT&CK | [attack.mitre.org](https://attack.mitre.org) | Adversarial tactics taxonomy |
| CVE Database | [cve.org](https://www.cve.org) | Vulnerability reference for security auditor |
| failspy/abliterator | [huggingface.co/failspy/abliterator](https://huggingface.co/failspy/abliterator) | Model censorship removal technique |

### Distributed & Agent Infrastructure

| Project | Link | Influence on uAI |
|---------|------|-----------------|
| Erlang/OTP | [erlang.org](https://www.erlang.org) | Actor model — each agent is an isolated process |
| Celery | [docs.celeryq.dev](https://docs.celeryq.dev) | Distributed task queue pattern |
| ZeroMQ | [zeromq.org](https://zeromq.org) | Message broker patterns for inter-agent communication |
| River (message broker) | [riverqueue.com](https://riverqueue.com) | Go-based task queue alternative |

### Philosophical & Architectural

| Project | Link | Influence on uAI |
|---------|------|-----------------|
| Dark City (film, 1998) | Wikipedia | Core metaphor — constructed reality, Tuning, Strangers |
| Platonic Cave Allegory | Wikipedia | Hidden reality, limited perspective per layer |
| Bostrom's Simulation Argument | Wikipedia | Nested reality possibility — Russian doll simulation |
| LessWrong — Subagents | [lesswrong.com](https://www.lesswrong.com/tag/subagents) | Mind-as-society-of-agents concept |
| Roko's Basilisk | LessWrong | Information hazard concept — knowledge asymmetries are power |

---

## Development Tools

| Tool | Link | Use |
|------|------|-----|
| Claude (OpenCode) | [opencode.ohmyopen.com](https://opencode.ohmyopen.com) | Primary development AI + orchestration |
| OpenRouter | [openrouter.ai](https://openrouter.ai) | (optional) Cloud model fallback on lil faegola |
| JetBrains Mono | [jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/) | Code/monospace font in docs |
| Inter | [rsms.me/inter](https://rsms.me/inter/) | UI font in docs |

---

## Ollama Model Installation

```bash
# Primary model (brain of the system)
ollama pull huihui_ai/qwen3.5-abliterated:9b

# Secondary ensemble models
ollama pull dolphin3:8b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
```

---

## Related

- [[local-vs-custom-decision-matrix]] — When to use each model
- [[models-and-amalgamations]] — Full model catalog
- [[../Architecture/Overview|Architecture Overview]] — Architectural context for the full stack
