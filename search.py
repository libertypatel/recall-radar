import os
import json
import time
import hashlib
import requests

CPSC_URL = "https://www.saferproducts.gov/RestWebServices/Recall"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "application/json",
}
SEARCH_CACHE_DIR = "search_cache"
CACHE_HOURS = 24
SNAPSHOT_PATH = "recalls_snapshot.json"


class SourceUnavailable(Exception):
    """Raised when CPSC can't be reached, so callers never mistake a failure for 'no recalls'."""

def is_error_response(data):
    """CPSC sometimes sends its own errors disguised as a recall with RecallID 0. Detect that."""
    if not isinstance(data, list):
        return True
    for record in data:
        title = str(record.get("Title") or "")
        if record.get("RecallID") == 0 or title.startswith("Error retrieving"):
            return True
    return False

def cpsc_query(**params):
    """Run one CPSC search with a 24-hour cache and up to 3 attempts."""
    params["format"] = "json"
    key = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    path = os.path.join(SEARCH_CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".json")

    # Use a recent cached answer if we have one
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_HOURS * 3600:
        with open(path) as f:
            return json.load(f)

    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(CPSC_URL, params=params, headers=HEADERS, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if is_error_response(data):
                    last_error = "CPSC returned an internal error"
                else:
                    print(f"CPSC {key}: {len(data)} results")  # temporary, to watch what CPSC returns
                    os.makedirs(SEARCH_CACHE_DIR, exist_ok=True)
                    with open(path, "w") as f:
                        json.dump(data, f)
                    return data
            else:
                last_error = f"status {response.status_code}"
        except (requests.RequestException, ValueError) as error:
            last_error = str(error)
        time.sleep(2 * (attempt + 1))  # wait 2s, then 4s, before trying again

    raise SourceUnavailable(f"CPSC could not be reached ({last_error})")


def recall_text(recall):
    """Combine a recall's title, description, and product names into one lowercase string."""
    parts = [recall.get("Title") or "", recall.get("Description") or ""]
    for product in recall.get("Products") or []:
        parts.append(product.get("Name") or "")
    return " ".join(parts).lower()


def search_recalls(details, max_results=5):
    """Search the saved CPSC copy first (fast and reliable). Use live CPSC only if no copy exists."""
    if os.path.exists(SNAPSHOT_PATH):
        candidates, saved_on = search_snapshot(details, max_results)
        note = (f"Saved copy of CPSC recall notices from 2020 through {saved_on}. "
                f"Recalls announced after that date are not included.")
        return candidates, note
    return search_live(details, max_results), "Live CPSC recall database"


def rank(found, details, max_results):
    """Score recalls: brand match counts most, then each product word. Return the top matches."""
    brand = details.get("brand")
    product_type = details.get("product_type")
    scored = []
    for recall in found.values():
        text = recall_text(recall)
        score = 0
        if brand and brand.lower() in text:
            score += 10
        if product_type:
            for word in product_type.lower().split():
                if word in text:
                    score += 1
        scored.append((score, recall))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [recall for score, recall in scored[:max_results] if score > 0]


def search_live(details, max_results=5):
    """Search the live CPSC database by brand and product type."""
    found = {}
    if details.get("brand"):
        for recall in cpsc_query(Title=details["brand"]):
            found[recall["RecallID"]] = recall
    if details.get("product_type"):
        for recall in cpsc_query(ProductName=details["product_type"]):
            found[recall["RecallID"]] = recall
    return rank(found, details, max_results)


def search_snapshot(details, max_results=5):
    """Search the saved copy of CPSC recalls. Returns (matches, date the copy was saved)."""
    with open(SNAPSHOT_PATH) as f:
        snapshot = json.load(f)
    found = {recall["RecallID"]: recall for recall in snapshot["recalls"]}
    return rank(found, details, max_results), snapshot["saved_on"]


def search_recalls(details, max_results=5):
    """Try live CPSC first, then fall back to the saved copy. Returns (candidates, source note)."""
    try:
        return search_live(details, max_results), "Live CPSC recall database"
    except SourceUnavailable:
        if not os.path.exists(SNAPSHOT_PATH):
            raise
        candidates, saved_on = search_snapshot(details, max_results)
        note = (f"Live CPSC search was unavailable, so this check used a saved copy of "
                f"CPSC recalls from 2020 onward, saved on {saved_on}.")
        return candidates, note


if __name__ == "__main__":
    candidates, source = search_recalls({"brand": "Voomf", "product_type": "crib mattress"})
    print("Source:", source)
    print("Candidates found:", len(candidates))
    for recall in candidates:
        print("-", recall.get("Title"))