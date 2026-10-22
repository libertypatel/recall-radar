import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)

TEXT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
CACHE_DIR = "scope_cache"

INSTRUCTIONS = """You read a product recall notice and extract exactly what is recalled.
Reply with only JSON, no other text, in this shape:
{
  "affected_models": [{"value": "...", "quote": "..."}],
  "dates": [{"type": "sold" or "manufactured" or "other", "as_written": "...", "quote": "..."}],
  "identification": [{"instruction": "...", "quote": "..."}],
  "remedy": [{"text": "...", "quote": "..."}]
}
Rules:
- Every "quote" must be copied word for word from the notice. Never paraphrase a quote.
- Only include what the notice states. Never guess.
- Use an empty list when the notice says nothing for that key."""


def notice_text(recall):
    """Build one readable text block from the parts of a CPSC recall record."""
    parts = [
        "Title: " + (recall.get("Title") or ""),
        "Description: " + (recall.get("Description") or ""),
    ]
    for product in recall.get("Products") or []:
        parts.append("Product: " + " ".join(
            str(product.get(key) or "") for key in ["Name", "Description", "Model", "NumberOfUnits"]
        ))
    for remedy in recall.get("Remedies") or []:
        parts.append("Remedy: " + (remedy.get("Name") or ""))
    for hazard in recall.get("Hazards") or []:
        parts.append("Hazard: " + (hazard.get("Name") or ""))
    for retailer in recall.get("Retailers") or []:
        parts.append("Sold at: " + (retailer.get("Name") or ""))
    return "\n".join(parts)


def normalize(text):
    """Lowercase, drop quote-mark characters, and collapse spaces, so only real wording differences fail."""
    for mark in ['"', "'", "`", "\u201c", "\u201d", "\u2018", "\u2019"]:
        text = text.replace(mark, "")
    return " ".join(text.lower().split())


def check_quotes(scope, source):
    """Mark every item supported (True) only if its quote really appears in the notice."""
    clean_source = normalize(source)
    for key in ["affected_models", "dates", "identification", "remedy"]:
        for item in scope.get(key, []):
            quote = item.get("quote") or ""
            item["supported"] = bool(quote) and normalize(quote) in clean_source
    return scope


def extract_scope(recall):
    """Return the structured, quote-checked scope for one recall, using the cache if available."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{recall['RecallID']}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    source = notice_text(recall)
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": source},
        ],
    )
    reply = response.choices[0].message.content.strip()
    if reply.startswith("```"):
        reply = reply.strip("`").removeprefix("json").strip()

    scope = check_quotes(json.loads(reply), source)
    scope["recall_id"] = recall["RecallID"]
    scope["title"] = recall.get("Title")
    scope["url"] = recall.get("URL")

    with open(cache_path, "w") as f:
        json.dump(scope, f, indent=2)
    return scope


if __name__ == "__main__":
    from search import search_recalls

    candidates = search_recalls({"brand": "Voomf", "product_type": "crib mattress"})
    scope = extract_scope(candidates[0])

    print("Recall:", scope["title"])
    for key in ["affected_models", "dates", "identification", "remedy"]:
        print(f"\n{key}:")
        for item in scope[key]:
            mark = "OK " if item["supported"] else "NOT SUPPORTED"
            print(f"  [{mark}] {item}")