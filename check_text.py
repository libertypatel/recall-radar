import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)

TEXT_MODEL = "nvidia/nemotron-3-super-120b-a12b"

listing = "Graco Pack n Play playard, gray, barely used, model 1234567, $40, pickup only"

start = time.time()
response = client.chat.completions.create(
    model=TEXT_MODEL,
    messages=[
        {"role": "system", "content": "Extract product details. Reply with only JSON with keys: brand, product, model_number, manufacture_date. Use null for anything not stated."},
        {"role": "user", "content": listing},
    ],
)
seconds = time.time() - start

print(response.choices[0].message.content)
print(f"Took {seconds:.1f} seconds")
print("Tokens used:", response.usage.total_tokens)