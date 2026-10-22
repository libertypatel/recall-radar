import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads NEBIUS_API_KEY from your .env file

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)

# Ask Token Factory for every model, then print only NVIDIA ones
for model in client.models.list():
    if "nvidia" in model.id.lower() or "nemotron" in model.id.lower():
        print(model.id)