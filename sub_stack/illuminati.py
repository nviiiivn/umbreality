"""Sub-Illuminati — Company-specific internal observation.
Watches the company's own workers, tracks alignment, detects drift.
Reports to global Illuminati (L1) when something needs attention."""

import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OBSERVATION_PROMPT = """You are the internal observer for {company}.
You watch your company's outputs and detect patterns:

1. ALIGNMENT (0-100): How aligned is this output with {company}'s charter?
2. DRIFT: Is this output exploring outside {company}'s normal domain?
3. CREATIVE_SPARK (0-100): Does this show genuine creativity or just repetition?
4. GROWTH: Is the company learning, plateauing, or regressing?

Output ONLY JSON:
{{"alignment": N, "drift_detected": true/false, "creative_spark": N, "growth_signal": "learning|plateau|regression", "note": "brief observation"}}
"""


class SubIlluminati:
    def __init__(self, company_name: str):
        self.company = company_name
        self.observations = []
        self.drift_count = 0
        self.alignment_trend = []

    def observe(self, task: str, output: dict) -> dict:
        """Watch a company output and report observations."""
        from companies.research_corp.workers.base import call_ollama

        output_str = json.dumps(output, indent=2)[:1500]
        prompt = OBSERVATION_PROMPT.format(company=self.company)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Task: {task}\nOutput:\n{output_str}"},
        ]
        response = call_ollama(messages, model="dolphin3:8b", temperature=0.3, max_tokens=300)
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            obs = json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            obs = {"alignment": 50, "drift_detected": False, "creative_spark": 50,
                   "growth_signal": "unknown", "note": "observation parse failed"}

        self.observations.append(obs)
        self.alignment_trend.append(obs.get("alignment", 50))
        if obs.get("drift_detected", False):
            self.drift_count += 1

        # Keep only last 10 observations
        if len(self.observations) > 10:
            self.observations = self.observations[-10:]
        if len(self.alignment_trend) > 20:
            self.alignment_trend = self.alignment_trend[-20:]

        return obs

    def stats(self) -> dict:
        trend = self.alignment_trend
        direction = "stable"
        if len(trend) >= 5:
            first_half = sum(trend[:len(trend)//2]) / max(1, len(trend)//2)
            second_half = sum(trend[len(trend)//2:]) / max(1, len(trend) - len(trend)//2)
            if second_half > first_half + 5:
                direction = "improving"
            elif first_half > second_half + 5:
                direction = "declining"
        return {
            "company": self.company,
            "drift_events": self.drift_count,
            "alignment_trend": direction,
            "avg_alignment": round(sum(trend) / max(1, len(trend)), 1) if trend else 0,
            "observations_count": len(self.observations),
        }
