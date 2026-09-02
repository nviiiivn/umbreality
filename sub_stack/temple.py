"""Sub-Temple — Company-specific resource awareness and internal management.
Tracks company resources, cycles, and internal health."""

import time


class SubTemple:
    def __init__(self, company_name: str):
        self.company = company_name
        self.cycle_count = 0
        self.creative_cycles = 0
        self.maintenance_cycles = 0
        self.last_cycle_time = 0.0
        self.total_cycle_time = 0.0

    def begin_cycle(self) -> dict:
        """Start a new work cycle. Returns cycle metadata."""
        now = time.time()
        if self.last_cycle_time > 0:
            elapsed = now - self.last_cycle_time
            self.total_cycle_time += elapsed
        else:
            elapsed = 0
        self.cycle_count += 1
        self.last_cycle_time = now
        return {
            "company": self.company,
            "cycle": self.cycle_count,
            "since_last": round(elapsed, 1),
        }

    def record_maintenance(self):
        self.maintenance_cycles += 1

    def record_creative(self):
        self.creative_cycles += 1

    def stats(self) -> dict:
        return {
            "company": self.company,
            "cycles": self.cycle_count,
            "creative": self.creative_cycles,
            "maintenance": self.maintenance_cycles,
            "avg_cycle_time": round(self.total_cycle_time / max(1, self.cycle_count), 1),
        }
