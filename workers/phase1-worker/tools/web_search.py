"""Web Search Tool — UmbrealityAI Worker
Uses DuckDuckGo for web search, no API key needed.
"""

from ddgs import DDGS


def web_search(query: str, num_results: int = 5) -> dict:
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=min(num_results, 10)))
        results = [{"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")} for r in raw]
        return {"tool": "web_search", "query": query, "num_results": len(results), "success": True, "results": results, "error": None}
    except Exception as e:
        return {"tool": "web_search", "query": query, "num_results": 0, "success": False, "results": [], "error": str(e)}


def format_results(results: dict) -> str:
    if not results.get("success"):
        return f"Search failed: {results.get('error', 'unknown error')}"
    items = results.get("results", [])
    if not items:
        return "No results found."
    return "\n\n".join(f"{i}. {r['title']}\n   {r['snippet']}\n   {r['url']}" for i, r in enumerate(items, 1))
