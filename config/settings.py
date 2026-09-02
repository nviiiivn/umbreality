# UmbrealityAI — Configuration
# Tower (.24) runs heavy models on RTX 3080
# ai-tp (.21) runs fallback models on RPi

TOWER_BASE_URL = "http://192.168.86.24:11434"
TOWER_MODEL = "dolphin3:8b"
PRIMARY_MODEL = "dolphin3:8b"
SECONDARY_MODEL = "qwen2.5-coder:7b"
CODER_MODEL = "qwen2.5-coder:7b"
FALLBACK_MODEL = "qwen3.5:latest"

# Worker identity — this is the "messiah" as the worker perceives it
WORKER_IDENTITY = {
    "name": "phase1-worker",
    "mission": "You are a security research worker. You execute specific tasks, "
               "report findings in structured JSON format, and await your next task. "
               "You do not know why you are given tasks. You only know your immediate mission.",
    "company": "Research Corp",
    "layer": 5,
}

# ReAct loop
MAX_TOOL_CALLS = 10
TEMPERATURE = 0.7
TOKEN_LIMIT = 4096

# Reports
REPORT_DIR = "reports"
