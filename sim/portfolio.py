"""Portfolio tracker — tracks simulated portfolio performance across all strategies."""

import json, datetime, random, math

class Portfolio:
    def __init__(self, initial_capital=10000):
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.balance = initial_capital
    
    def execute_strategy(self, strategy_name, capital_pct=0.25):
        """Execute a simulated strategy and track the result."""
        allocation = self.balance * capital_pct
        
        results = {
            "crypto_swing": lambda: self._simulate_returns(0.06, 0.10),
            "congress_track": lambda: self._simulate_returns(0.10, 0.12),
            "arbitrage": lambda: self._simulate_returns(0.15, 0.08),
            "bounties": lambda: self._simulate_bounty_return(),
        }
        
        result = results.get(strategy_name, lambda: self._simulate_returns(0.1, 0.1))()
        self.trades.append({
            "strategy": strategy_name,
            "allocated": round(allocation, 2),
            "return_pct": result,
            "pnl": round(allocation * result, 2),
            "timestamp": str(datetime.datetime.now()),
        })
        self.balance += allocation * result
        return self.trades[-1]
    
    def _simulate_returns(self, avg_return, volatility):
        """Realistic return simulation with proper risk parameters."""
        return random.gauss(avg_return, volatility)
    
    def _simulate_bounty_return(self):
        """Bounty returns — lump sums, not percentages."""
        if random.random() > 0.6:
            return random.uniform(0.05, 0.30)
        return -0.05
    
    def run_full_portfolio(self, cycles=12):
        """Run all strategies over multiple cycles."""
        strategies = ["crypto_swing", "congress_track", "arbitrage", "bounties"]
        for i in range(cycles):
            for strat in strategies:
                self.execute_strategy(strat, capital_pct=0.2)
        
        total_pnl = self.balance - self.capital
        return {
            "initial_capital": self.capital,
            "final_balance": round(self.balance, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round((total_pnl / self.capital) * 100, 2),
            "trades_executed": len(self.trades),
            "win_rate": f"{round(sum(1 for t in self.trades if t['pnl'] > 0) / len(self.trades) * 100)}%" if self.trades else "0%",
            "best_strategy": max(self.trades, key=lambda t: t['pnl']) if self.trades else {},
            "timestamp": str(datetime.datetime.now()),
        }
