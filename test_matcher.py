import json
from matcher import match_recall, clean_model

with open("scope_cache/10904.json") as f:
    SCOPE = json.load(f)


def test_exact_model_matches():
    assert match_recall({"brand": "Voomf", "model_number": "BYL001"}, SCOPE)["result"] == "match_supported"


def test_model_format_differences_still_match():
    assert match_recall({"brand": "voomf", "model_number": "byl-001"}, SCOPE)["result"] == "match_supported"


def test_different_model_is_outside_scope():
    assert match_recall({"brand": "Voomf", "model_number": "BYL002"}, SCOPE)["result"] == "outside_scope"


def test_missing_model_needs_info_never_safe():
    outcome = match_recall({"brand": "Voomf", "model_number": None}, SCOPE)
    assert outcome["result"] == "info_needed"
    assert "model number" in outcome["missing"]


def test_missing_brand_needs_info():
    outcome = match_recall({"brand": None, "model_number": "BYL001"}, SCOPE)
    assert outcome["result"] == "info_needed"
    assert "brand" in outcome["missing"]


def test_different_brand_is_outside_scope():
    assert match_recall({"brand": "Graco", "model_number": "BYL001"}, SCOPE)["result"] == "outside_scope"


def test_unverified_models_are_never_used_for_a_match():
    fake_scope = {
        "title": "Voomf recall",
        "url": "",
        "affected_models": [{"value": "BYL001", "quote": "made up", "supported": False}],
    }
    outcome = match_recall({"brand": "Voomf", "model_number": "BYL001"}, fake_scope)
    assert outcome["result"] == "info_needed"


def test_clean_model_ignores_spaces_dashes_and_case():
    assert clean_model("byl-001") == clean_model("BYL 001") == "BYL001"