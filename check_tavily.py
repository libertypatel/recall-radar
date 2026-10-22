import os
import time
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

query = "Voomf play yard crib mattress recall BYL001"

start = time.time()
results = client.search(query, max_results=3)
seconds = time.time() - start

for r in results["results"]:
    print("\nTitle:", r["title"])
    print("URL:", r["url"])
    print("Snippet:", r["content"][:200])

print(f"\nTook {seconds:.1f} seconds")