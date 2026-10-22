import requests

CPSC_URL = "https://www.saferproducts.gov/RestWebServices/Recall"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "application/json",
}


def cpsc_query(**params):
    """Run one CPSC search and return the list of recalls (empty list on failure)."""
    params["format"] = "json"
    response = requests.get(CPSC_URL, params=params, headers=HEADERS, timeout=30)
    if response.status_code != 200:
        print("CPSC search failed:", response.status_code)
        return []
    return response.json()


def recall_text(recall):
    """Combine a recall's title, description, and product names into one lowercase string."""
    parts = [recall.get("Title") or "", recall.get("Description") or ""]
    for product in recall.get("Products") or []:
        parts.append(product.get("Name") or "")
    return " ".join(parts).lower()


def search_recalls(details, max_results=5):
    """Search CPSC using extracted listing details and return the best-matching recalls."""
    brand = details.get("brand")
    product_type = details.get("product_type")

    # Collect results from both searches, keyed by RecallID so nothing is counted twice
    found = {}
    if brand:
        for recall in cpsc_query(Title=brand):
            found[recall["RecallID"]] = recall
    if product_type:
        for recall in cpsc_query(ProductName=product_type):
            found[recall["RecallID"]] = recall

    # Score each recall: brand match counts most, then each product word that appears
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


if __name__ == "__main__":
    details = {"brand": "Voomf", "product_type": "crib mattress"}
    candidates = search_recalls(details)
    print("Candidates found:", len(candidates))
    for recall in candidates:
        print("\n-", recall.get("Title"))
        print(" ", recall.get("URL"))