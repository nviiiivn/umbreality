# UmbrealityAI — Configuration
# Tower Ollama endpoint: http://192.168.86.24:11434

TOWER_BASE_URL = "http://192.168.86.24:11434"
PRIMARY_MODEL = "huihui_ai/qwen3.5-abliterated:9b"
SECONDARY_MODEL = "dolphin3:8b"

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
