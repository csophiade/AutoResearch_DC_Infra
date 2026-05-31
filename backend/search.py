from __future__ import annotations
import os
from backend.config import settings

def search_web(query: str, max_results: int = 4) -> list[dict]:
    """
    Search the web for a query. Plugs into Tavily if an API key is available,
    otherwise falls back to DuckDuckGo (no API key required).
    
    Returns a list of dicts with:
    - title: title of the page
    - url: source URL
    - content: text snippet/content
    """
    print(f"[SEARCH] Query: '{query}'")
    
    # 1. Tavily Search (preferred if API key is provided)
    if settings.has_tavily:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            response = client.search(query=query, max_results=max_results, search_depth="basic")
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })
            print(f"[SEARCH] Tavily returned {len(results)} results.")
            return results
        except Exception as e:
            print(f"[SEARCH] Tavily failed: {e}. Falling back to DuckDuckGo.")
            
    # 2. DuckDuckGo Search (zero-config fallback)
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=max_results))
            results = []
            for item in ddg_results:
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("href", ""),
                    "content": item.get("body", "")
                })
            print(f"[SEARCH] DuckDuckGo returned {len(results)} results.")
            return results
    except Exception as e:
        print(f"[SEARCH] DuckDuckGo fallback failed: {e}")
        
    # Return empty list if all fail
    return []
