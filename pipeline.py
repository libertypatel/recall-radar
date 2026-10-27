from matcher import clean_model
from extract import extract_listing
from search import search_recalls, SourceUnavailable
from scope import extract_scope
from matcher import match_recall
from questions import seller_questions

MAX_QUESTION_SETS = 2  # only write seller questions for the top 2 unresolved recalls, to save calls


def summarize(results):
    """Turn the per-recall results into one overall headline. Never says 'safe'."""
    kinds = [r["result"] for r in results]
    if "match_supported" in kinds:
        return "Recall match supported"
    if "info_needed" in kinds:
        return "Possible match: specific information needed"
    if results:
        return f"Outside the scope of the {len(results)} recall notice(s) checked"
    return "No matching recall found in the sources checked"


def check_details(details):
    """Run search, scope, and matching for already-extracted details."""
    try:
        candidates = search_recalls(details)
    except SourceUnavailable as error:
        return {
            "details": details,
            "summary": "Could not reach the CPSC recall database, so no conclusion was made. Please try again.",
            "results": [],
            "error": str(error),
        }

    results = []
    question_sets = 0
    for recall in candidates:
        scope = extract_scope(recall)
        outcome = match_recall(details, scope)
        outcome["questions"] = []
        if outcome["result"] == "info_needed" and question_sets < MAX_QUESTION_SETS:
            outcome["questions"] = seller_questions(outcome, scope)
            question_sets += 1
        outcome["scope"] = scope
        results.append(outcome)
    return {"details": details, "summary": summarize(results), "results": results}

FIELDS = ["brand", "product_type", "model_number", "manufacture_date"]


def same_value(field, a, b):
    """Compare two values loosely: model numbers ignore dashes/spaces/case, others ignore case."""
    if field == "model_number":
        return clean_model(a) == clean_model(b)
    return str(a).strip().lower() == str(b).strip().lower()


def merge_details(details, reply_details):
    """Fill missing fields from the seller's reply. Never overwrite a conflicting value; report it instead."""
    merged = dict(details)
    conflicts = []
    for field in FIELDS:
        new = reply_details.get(field)
        old = details.get(field)
        if not new:
            continue
        if not old:
            merged[field] = new
        elif not same_value(field, old, new):
            conflicts.append({"field": field, "listing": old, "reply": new})
    return merged, conflicts

def check_listing(listing_text):
    """Full check starting from pasted listing text."""
    details = extract_listing(listing_text)
    return check_details(details)


if __name__ == "__main__":
    listing = "Voomf crib mattress, white with balloon print, fits pack n play. Barely used, $15."
    report = check_listing(listing)

    print("Details:", report["details"])
    print("\nSUMMARY:", report["summary"])
    for r in report["results"]:
        print(f"\n[{r['result']}] {r['title'][:80]}")
        for reason in r["reasons"]:
            print("   -", reason)
        for q in r["questions"]:
            print("   Ask seller:", q)