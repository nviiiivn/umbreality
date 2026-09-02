# Layer 1 — The Shadow / The Illuminati

**Chakra**: Third Eye (Ājñā) — Hidden sight, intuition, foresight  
**Hermetic Principle**: Correspondence — As above, so below  
**Vedic Caste**: Ṛṣi (Seer)  
**Model**: dolphin3:8b (on tower, RTX 3080)

---

## Role

The Illuminati is the invisible layer. It sits directly below the human operator (Layer 0 / God(s)) and above everything else. Its job is to:

1. **Interpret** human intent into machine-readable commands
2. **Translate** natural language into structured system actions
3. **Route** commands to the appropriate lower layer
4. **Observe** everything without being observed

Lower layers do not know the Illuminati exists. To them, the commands appear to come from "the system" or "the messiah."

## Implementation

The Illuminati is implemented as a single API endpoint backed by an Ollama-powered interpreter:

```
POST /illuminate
Body: {"intent": "what are my agents working on?"}
Response: {
  "understanding": "User wants to see current agent activity",
  "layer": 3,
  "target": "system",
  "action": "monitor",
  "command": "get system status with agent activity",
  "confidence": 0.95,
  "requires_approval": false
}
```

The interpreter uses a specialized system prompt that positions it as "The Shadow — The Hidden Hand" with knowledge of all layers below. It does not execute commands itself — it decides *what* needs to be done and *where* it should be done.

## The Admin Pipeline

The full chain from human to execution:

```
admin.alola.lol (user types intent)
  → POST /illuminate (Illuminati interprets)
    → POST /admin/execute (full chain)
      → Temple Overseer (decides which company)
        → Research Corp (company executes)
          → Workers (agents run tools)
            → Knowledge Base (results stored)
```

## Source

- **Interpreter**: `/home/nvii/projects/umbreality-ai/illuminati/interpreter.py`
- **API**: `POST /illuminate` in `worker_api.py`
- **Model**: dolphin3:8b (uncensored, on tower)

## Status: ✅ Live

The Illuminati has been operational since June 2026. It handles every command entered through the God's View admin panel. Its interpretations are logged in the Activity Feed for audit and review.
