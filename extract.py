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

INSTRUCTIONS = """You extract product details from secondhand listings.
Reply with only JSON, no other text, using these keys:
brand, product_type, model_number, manufacture_date, other_identifiers.
Use null for anything the listing does not state. Never guess."""


def extract_listing(listing_text):
    """Send listing text to Nemotron and return the details as a Python dictionary."""
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": listing_text},
        ],
    )
    reply = response.choices[0].message.content.strip()

    # Models sometimes wrap JSON in ```json fences, so remove them if present
    if reply.startswith("```"):
        reply = reply.strip("`").removeprefix("json").strip()

    return json.loads(reply)


# This part only runs when you run this file directly, so we can test it
if __name__ == "__main__":
    sample = "Voomf crib mattress, white with balloon print, fits pack n play. Barely used, $15."
    details = extract_listing(sample)
    print(details)
    print("Brand:", details["brand"])
    print("Model number:", details["model_number"])