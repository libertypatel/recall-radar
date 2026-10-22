import re


def clean_model(text):
    """Uppercase and keep only letters and digits, so 'byl-001' and 'BYL 001' both become 'BYL001'."""
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def match_recall(details, scope):
    """Compare listing details to one recall's verified scope and return a result with reasons."""
    reasons = []
    missing = []
    outside = []

    # Only criteria that passed the quote check can be used
    models = [item for item in scope.get("affected_models", []) if item.get("supported")]
    unverified = [item for item in scope.get("affected_models", []) if not item.get("supported")]
    notice_text = ((scope.get("title") or "") + " " + (scope.get("url") or "")).lower()

    # Brand check
    brand = details.get("brand")
    if not brand:
        missing.append("brand")
    elif brand.lower() not in notice_text:
        outside.append(f"Brand '{brand}' does not appear in this recall notice.")
    else:
        reasons.append(f"Brand '{brand}' matches this recall notice.")

    # Model number check
    listing_model = clean_model(details.get("model_number"))
    recall_models = [clean_model(item["value"]) for item in models]

    if not models:
        if unverified:
            reasons.append("This notice's model numbers could not be verified against the source text.")
        else:
            reasons.append("This notice does not list model numbers.")
        missing.append("a way to confirm the exact product (check the notice's identification details)")
    elif not listing_model:
        missing.append("model number")
        reasons.append("Recalled models: " + ", ".join(item["value"] for item in models))
    elif listing_model in recall_models:
        reasons.append(f"Model {details['model_number']} is listed in this recall.")
    else:
        outside.append(f"Model {details['model_number']} is not among the recalled models: "
                       + ", ".join(item["value"] for item in models))

    # Decide: outside beats everything, then missing info, otherwise a supported match
    if outside:
        result = "outside_scope"
        reasons = outside + reasons
    elif missing:
        result = "info_needed"
    else:
        result = "match_supported"

    return {
        "recall_id": scope.get("recall_id"),
        "title": scope.get("title"),
        "url": scope.get("url"),
        "result": result,
        "reasons": reasons,
        "missing": missing,
    }


if __name__ == "__main__":
    import json

    with open("scope_cache/10904.json") as f:
        scope = json.load(f)

    tests = [
        ("Exact model", {"brand": "Voomf", "model_number": "BYL001"}),
        ("Same model, different format", {"brand": "voomf", "model_number": "byl-001"}),
        ("Different model", {"brand": "Voomf", "model_number": "BYL002"}),
        ("No model in listing", {"brand": "Voomf", "model_number": None}),
        ("Different brand", {"brand": "Graco", "model_number": "BYL001"}),
    ]

    for name, details in tests:
        outcome = match_recall(details, scope)
        print(f"\n{name}: {outcome['result']}")
        for reason in outcome["reasons"]:
            print("  -", reason)
        if outcome["missing"]:
            print("  Missing:", ", ".join(outcome["missing"]))