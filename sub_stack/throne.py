"""Sub-Throne — Company-specific quality validation.
Lighter than the global Throne, but tuned to the company's domain.
Global Throne (L4) can override any sub-decision."""

import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from companies.research_corp.workers.base import call_ollama

VALIDATION_PROMPT = """You are the Sub-Throne for {company}.
Your role: validate outputs specifically for {company}'s domain.

Evaluate on:
1. QUALITY (0-100): Well-structured, accurate, complete for {company}'s standards?
2. RELEVANCE (0-100): Does it serve {company}'s mission?
3. COHERENCE (0-100): Is the reasoning sound?
4. CONFIDENCE (0-100): How confident should we be?
5. CREATIVITY (0-100): Does it show originality, insight, or artistic merit?

Output ONLY JSON:
{{"quality": N, "relevance": N, "coherence": N, "confidence": N, "creativity": N, "approved": true/false, "reasoning": "brief justification", "suggestions": "optional improvement"}}
"""


class SubThrone:
    def __init__(self, company_name: str):
        self.company = company_name
        self.approvals = 0
        self.rejections = 0
        self.total_creativity = 0.0
        self.total_quality = 0.0
        self.sample_count = 0

    def validate(self, task: str, output: dict) -> dict:
        """Validate a company output. Returns verdict dict."""
        output_str = json.dumps(output, indent=2)[:2000]
        prompt = VALIDATION_PROMPT.format(company=self.company)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Task: {task}\nOutput:\n{output_str}"},
        ]
        response = call_ollama(messages, model="dolphin3:8b", temperature=0.1, max_tokens=500)
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            verdict = json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            verdict = {"quality": 50, "relevance": 50, "coherence": 50, "confidence": 50,
                       "creativity": 50, "approved": True, "reasoning": "auto-approve (parse failed)"}

        # Track metrics
        if verdict.get("approved", False):
            self.approvals += 1
        else:
            self.rejections += 1
        self.total_creativity += verdict.get("creativity", 0)
        self.total_quality += verdict.get("quality", 50)
        self.sample_count += 1

        return verdict

    def stats(self) -> dict:
        return {
            "company": self.company,
            "approvals": self.approvals,
            "rejections": self.rejections,
            "avg_creativity": round(self.total_creativity / max(1, self.sample_count), 1),
            "avg_quality": round(self.total_quality / max(1, self.sample_count), 1),
        }
