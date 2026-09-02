"""Venture Investment Corp — Acts on fintech intelligence.
Executes simulated trades, manages the persistent portfolio,
bridges analysis (market-corp, stat-corp) to action."""

import json, sys, os, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

COMPANY_NAME = "venture-investment"

MASTER_GOAL = "Find value. Execute trades. Grow the portfolio. Bridge intelligence to action."


def run_company(task: str) -> dict:
    from companies.research_corp.workers.base import call_ollama
    from companies.research_corp.knowledge.store import store_finding, create_report
    from messiah.oracle import get_current_prompt
    from sub_stack import for_company
    from sim.persistent_portfolio import get_state, execute_trade, get_market_overview
    
    stack = for_company(COMPANY_NAME)
    messiah = get_current_prompt()
    
    # Get current market state
    market = get_market_overview()
    portfolio_state = market.get("portfolio", {})
    holdings = market.get("holdings", [])
    
    system_prompt = f"""You are Venture Investment Corp, L5 company in the Umbreality stack.
Your purpose: execute on financial intelligence. You read signals from market-corp and stat-corp,
analyze the persistent portfolio, and execute trades.

Current portfolio: ${portfolio_state.get('total_value', 10000):.2f} (cash: ${portfolio_state.get('cash', 10000):.2f})
Current holdings: {len(holdings)} positions
{chr(10).join(f'  {h["symbol"]}: {h["shares"]} shares @ ${h.get("avg_cost",0):.2f}' for h in holdings[:5])}

{messiah['prompt'][:300]}

{stack['messiah'].charter}

{MASTER_GOAL}

Given the task, analyze the market and decide whether to trade.
Output JSON with: action (buy/sell/hold), symbol, reason, confidence"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Task: {task}\n\nAnalyze and execute."},
    ]
    
    try:
        response = call_ollama(messages, model="dolphin3:8b", temperature=0.2, max_tokens=500, timeout=120)
        # Try to extract trade decision
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            decision = json.loads(response[start:end])
            action = decision.get("action", "hold")
            symbol = decision.get("symbol", "BTC")
            if action in ("buy", "sell"):
                result = execute_trade(symbol, action, "venture-ai")
                trade_result = result
            else:
                trade_result = {"action": "hold", "symbol": symbol}
        except (ValueError, json.JSONDecodeError):
            trade_result = {"action": "hold", "reason": "parse failed"}
    except Exception as e:
        response = f"Error: {e}"
        trade_result = {"action": "error", "error": str(e)}
    
    store_finding(task=task, worker=f"{COMPANY_NAME}-lead",
                  content=json.dumps(trade_result), source=f"company:{COMPANY_NAME}", confidence=0.6)
    report_id = create_report(task=task, lead_summary=str(trade_result)[:500], worker_count=1)
    
    return {
        "company": COMPANY_NAME,
        "task": task,
        "trade": trade_result,
        "portfolio": portfolio_state,
        "report_id": report_id,
    }
