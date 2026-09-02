"""Research Corp — Lead Agent
Orchestrates workers, validates findings, produces final reports.
"""

import json, sys, os, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from .workers.base import BaseWorker, call_ollama
from .knowledge.store import store_finding, get_findings, create_report, get_reports, validate_finding

WORKERS = {
    "researcher": None,  # lazy import
    "reporter": None,
}


def _get_worker(name):
    if WORKERS[name] is None:
        if name == "researcher":
            from .workers.researcher import researcher as w
        elif name == "reporter":
            from .workers.reporter import reporter as w
        WORKERS[name] = w
    return WORKERS[name]


LEAD_SYSTEM = """You are the Lead Agent of Research Corp, a multi-worker AI company.

Your job:
1. Analyze incoming tasks and break them into subtasks
2. Assign subtasks to the right workers
3. Validate and aggregate results
4. Produce a final structured report

Available workers:
- researcher: web search + command execution
- reporter: compiles findings into structured reports

Respond in this format:
THOUGHT: your reasoning
ACTION: dispatch|validate|finalize
WORKER: worker_name (if dispatching)
TASK: subtask for worker
or
VALIDATE: finding_id
or
FINAL: {{"summary": "...", "findings": [...], "confidence": 0.9}}"""


def decompose_task(task, model=None):
    """Break a task into subtasks. Tries Ollama, falls back to simple dispatch."""
    msg = [{"role": "system", "content": "Output ONLY a JSON array. Example: [{\"worker\":\"researcher\",\"task\":\"find info about X\"}]"},
           {"role": "user", "content": f"Break this task into sub-tasks for researcher and reporter workers.\nTask: {task}\n\nJSON array:"}]
    try:
        response = call_ollama(msg, temperature=0.1, max_tokens=500, model=model or os.environ.get("UAI_MODEL", "qwen3.5:latest"))
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except Exception:
        pass
    return [{"worker": "researcher", "task": task}]


def run_company(task):
    """Execute a task through the company pipeline."""
    print(f"[Research Corp] Decomposing task: {task}")
    subtasks = decompose_task(task)
    print(f"[Research Corp] Generated {len(subtasks)} subtasks")

    all_findings = []
    for i, st in enumerate(subtasks):
        worker_name = st.get("worker", "researcher")
        subtask = st.get("task", task)
        print(f"[Research Corp] Subtask {i+1}: {worker_name} ← {subtask[:80]}")

        try:
            worker = _get_worker(worker_name)
            result = worker.run(subtask)
            print(f"[Research Corp] {worker_name} completed")

            # Store finding
            fid = store_finding(
                task=task,
                worker=worker_name,
                content=json.dumps(result) if isinstance(result, dict) else str(result),
                source=f"worker:{worker_name}",
                confidence=0.7,
                tags=[worker_name, "subtask"],
            )
            all_findings.append({"id": fid, "worker": worker_name, "result": result})
        except Exception as e:
            print(f"[Research Corp] {worker_name} failed: {e}")

    # Aggregate into report
    print(f"[Research Corp] Synthesizing final report...")
    context = {
        "task": task,
        "findings": all_findings,
        "finding_count": len(all_findings),
    }

    reporter = _get_worker("reporter")
    report = reporter.run(
        f"Synthesize a final structured report for: {task}",
        context=context,
    )

    rid = create_report(
        task=task,
        lead_summary=json.dumps(report) if isinstance(report, dict) else str(report),
        worker_count=len(all_findings),
    )

    return {
        "status": "complete",
        "task": task,
        "report_id": rid,
        "findings_count": len(all_findings),
        "report": report,
    }
