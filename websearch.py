import os
import json
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

CACHE_DIR = "tavily_cache"


def get_key():
    """Read the Tavily key from .env locally, or from Streamlit secrets when deployed."""
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets["TAVILY_API_KEY"]
        except Exception:
            key = None
    return key


def recall_web_sources(scope, max_results=3):
    """Search the web for extra sources about one recall. Returns a list, never raises."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{scope.get('recall_id')}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)

    key = get_key()
    if not key:
        return []
    try:
        client = TavilyClient(api_key=key)
        query = f"{scope.get('title')} recall manufacturer remedy"
        results = client.search(query, max_results=max_results, exclude_domains=["cpsc.gov"])
        sources = [
            {"title": r["title"], "url": r["url"], "snippet": r["content"][:300]}
            for r in results.get("results", [])
        ]
    except Exception:
        return []

    with open(path, "w") as f:
        json.dump(sources, f, indent=2)
    return sources


if __name__ == "__main__":
    scope = {"recall_id": 10904, "title": "Play Yard and Crib Mattresses Recalled ... Sold on Amazon by Voomf"}
    for s in recall_web_sources(scope):
        print("-", s["title"])
        print(" ", s["url"])