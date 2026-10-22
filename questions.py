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

INSTRUCTIONS = """You help a buyer of a used product ask the seller for missing details.
You get the details that are missing and the recall notice's identification instructions.
Write short, friendly questions the buyer can send the seller, such as asking for a photo of a specific label.
Only use locations and details from the identification instructions given. Never invent where a label is.
Reply with only JSON: {"questions": ["...", "..."]}. Use at most 3 questions."""


def seller_questions(outcome, scope):
    """Return a list of questions to send the seller, or an empty list if nothing is missing."""
    if outcome["result"] != "info_needed":
        return []

    # Only verified identification details can be used
    instructions = [item["instruction"] for item in scope.get("identification", []) if item.get("supported")]

    request = {
        "missing": outcome["missing"],
        "identification_instructions": instructions,
    }
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": json.dumps(request)},
        ],
    )
    reply = response.choices[0].message.content.strip()
    if reply.startswith("```"):
        reply = reply.strip("`").removeprefix("json").strip()
    return json.loads(reply)["questions"]


if __name__ == "__main__":
    from matcher import match_recall

    with open("scope_cache/10904.json") as f:
        scope = json.load(f)

    outcome = match_recall({"brand": "Voomf", "model_number": None}, scope)
    print("Result:", outcome["result"])
    for question in seller_questions(outcome, scope):
        print("-", question)