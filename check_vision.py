import os
import time
import base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)

VISION_MODEL = "nvidia/Nemotron-3.5-Super-VL"

# Turn the image into text so it can be sent in the request
with open("test_label.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

start = time.time()
response = client.chat.completions.create(
    model=VISION_MODEL,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Read this product label. Reply with only JSON with keys: brand, product, model_number, manufacture_date. Use null for anything not visible."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ],
        }
    ],
)
seconds = time.time() - start

print(response.choices[0].message.content)
print(f"Took {seconds:.1f} seconds")
print("Tokens used:", response.usage.total_tokens)