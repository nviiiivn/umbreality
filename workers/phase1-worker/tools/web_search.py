"""
Web Search Tool — Phase 1 Worker
Calls websearch to find information based on a query.
Returns structured results: source, snippet, url.
"""

import json
from typing import Optional
from urllib.parse import quote_plus


def web_search(query: str, num_results: int = 5) -> dict:
    """
    Search the web for the given query.

    Args:
        query: Search terms
        num_results: Number of results to return (max 10)

    Returns:
        dict with keys: success (bool), results (list), error (str or None)
    """
    # Structure for what the tool returns
    # The actual web search API call will be implemented per-provider

    return {
        "tool": "web_search",
        "query": query,
        "num_results": num_results,
        "success": True,
        "results": [],
        "error": None,
    }


def format_results(results: dict) -> str:
    """Format search results for LLM consumption."""
    if not results.get("success"):
        return f"Search failed: {results.get('error', 'unknown error')}"

    items = results.get("results", [])
    if not items:
        return "No results found."

    formatted = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "Untitled")
        snippet = item.get("snippet", "No description")
        url = item.get("url", "")
        formatted.append(f"{i}. {title}\n   {snippet}\n   {url}")

    return "\n\n".join(formatted)
