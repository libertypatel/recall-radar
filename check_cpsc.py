import requests

url = "https://www.saferproducts.gov/RestWebServices/Recall"
params = {"format": "json", "ProductName": "crib"}

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "application/json",
}
response = requests.get(url, params=params, headers=headers, timeout=30)
print("Content type:", response.headers.get("Content-Type"))
print("First 500 characters:", response.text[:500])
recalls = response.json()

print("Recalls found:", len(recalls))

first = recalls[0]
print("\nTitle:", first.get("Title"))
print("Date:", first.get("RecallDate"))
print("Link:", first.get("URL"))

for product in first.get("Products", []):
    print("\nProduct name:", product.get("Name"))
    print("Model field:", product.get("Model"))
    print("Description:", product.get("Description"))