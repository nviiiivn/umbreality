"""Reporter worker — synthesizes findings into structured reports."""

import json
from .base import BaseWorker, call_ollama


class ReportWorker(BaseWorker):
    def run(self, task, context=None):
        messages = [
            {"role": "system", "content": "You synthesize findings into structured JSON reports. "
             "Given context with findings, produce a report with: summary, key_findings, and recommendations. "
             "Output RESULT: <JSON>"},
        ]
        if context:
            findings = context.get("findings", [])
            ctx_str = json.dumps({k: v for k, v in context.items() if k != "findings"}, indent=2)
            if findings:
                ctx_str += f"\n\nFindings ({len(findings)}):\n"
                for f in findings:
                    ctx_str += f"\n- [{f.get('worker','?')}] {json.dumps(f.get('result',{}), indent=2)[:200]}"
            messages.append({"role": "user", "content": f"Context:\n{ctx_str}"})
        messages.append({"role": "user", "content": f"Task: {task}"})

        for step in range(5):
            response = call_ollama(messages, model=self.model, temperature=0.3)
            messages.append({"role": "assistant", "content": response})
            for line in response.split("\n"):
                if line.startswith("RESULT:"):
                    try:
                        return json.loads(line[len("RESULT:"):].strip())
                    except json.JSONDecodeError:
                        return {"raw": line[len("RESULT:"):].strip()}
            messages.append({"role": "user", "content": "Continue. Output RESULT: <JSON>"})
        return {"error": "max_steps"}


reporter = ReportWorker(name="Reporter", role_desc="report synthesis specialist", tools={})


def run(task, context=None):
    return reporter.run(task, context)
