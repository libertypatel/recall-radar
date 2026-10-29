# Recall Radar

**Before you buy used, find relevant recall evidence and learn exactly what to ask the seller.**

Live demo: https://recall-radar.streamlit.app

Built for the Nebius x NVIDIA Global AI Hackathon (Best Apps and Agents track) with **NVIDIA Nemotron on Nebius Token Factory** and **Tavily**.

## The problem

Recalled baby products keep getting resold on Facebook Marketplace, at yard sales, and in thrift stores. Recall notices usually apply to specific model numbers or date ranges, but secondhand listings rarely include those details. A buyer looking at "Voomf crib mattress, barely used, $15" has no easy way to know whether that exact item is affected, or what to ask before paying.

## What it does

1. **Paste a listing.** Nemotron reads the brand, product type, model number, and date. Anything not stated is left empty, never guessed.
2. **Find candidate recalls** from CPSC recall notices.
3. **Read each recall's scope.** Nemotron extracts the affected models, dates, identification instructions, and remedy, each with the exact quote it came from. Python then checks that every quote really appears in the notice. Anything that fails is marked unverified and is never used to declare a match.
4. **Match in plain Python, one result per recall:**
   - **Recall match supported**: the model number is on the verified list
   - **Possible match, information needed**: something the decision depends on is missing
   - **Outside this recall's scope**: a clear mismatch with this notice, such as a different model
   - **No matching recall found in the sources checked**: never "safe"
5. **Ask the seller.** When information is missing, Nemotron writes questions from the recall's verified identification instructions, such as "Could you send a photo of the label inside the mattress cover?" The questions never reveal the recalled model number, so the seller reports what the label actually says.
6. **Update with the seller's reply.** The reply fills in missing details and the result is rechecked. If the reply conflicts with the listing (for example, a different model number), the app shows the conflict and asks the buyer to confirm instead of overwriting.
7. **More sources from Tavily.** For recalls that may apply, Tavily finds manufacturer and news pages about that recall. These are shown as clearly labeled context and never change the result.

Results describe recall evidence only, never general product safety.

## How NVIDIA Nemotron and Nebius Token Factory are used

All model calls go to **`nvidia/nemotron-3-super-120b-a12b`** on Nebius Token Factory for three jobs:

| Step | File | What Nemotron does |
| --- | --- | --- |
| Listing extraction | `extract.py` | Turns free-text listings and seller replies into structured details |
| Recall scope extraction | `scope.py` | Turns a recall notice into structured criteria with supporting quotes |
| Seller questions | `questions.py` | Writes questions using only verified identification instructions |

The AI reads and extracts. It never makes the final decision: `matcher.py` is plain Python with unit tests.

**Where Token Factory helped:** its API is OpenAI-compatible, so the standard `openai` Python library worked by changing only the base URL. One key gave access to several Nemotron models, which let us test a text model and a vision model (`nvidia/Nemotron-3.5-Super-VL`, which correctly read a real product label in testing) before choosing what to build on. A first listing extraction took about 2.3 seconds and 247 tokens. Recall scopes are cached in `scope_cache/`, so each notice is read by the model only once.

## Engineering decisions

Building against real government data surfaced problems that shaped the design:

- **The CPSC API blocked plain scripts** (403 Access Denied) until requests sent browser-style headers.
- **CPSC returned its own server errors disguised as recall records** (RecallID 0, with an error message as the title). A naive app would read that as "no recalls found." Recall Radar detects these and treats them as an outage, never as an answer.
- **CPSC sometimes ignored the brand filter** and returned over 10,000 records, and one record merged two unrelated recalls into a single title. So the app never relies on a single field and always links the source notice.
- **A saved copy for reliability.** `build_snapshot.py` downloads CPSC recalls month by month (2,307 recalls from January 2020 through October 27, 2026, with no failed months). The app searches this copy so the demo stays fast and available, and it states the snapshot date on screen. Recalls announced after that date are not included.
- **Quote verification** ignores only quotation-mark styles, so wording must match exactly.

## Run it locally

Requires Python 3.13 and API keys for Nebius Token Factory and Tavily.

```bash
git clone https://github.com/libertypatel/recall-radar.git
cd recall-radar
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (it is excluded by `.gitignore`):

```
NEBIUS_API_KEY=your-token-factory-key
TAVILY_API_KEY=your-tavily-key
```

Start the app:

```bash
streamlit run app.py
```

Run the matcher tests:

```bash
pip install pytest
pytest
```

Refresh the saved CPSC copy (optional):

```bash
python build_snapshot.py
```

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit interface |
| `pipeline.py` | Runs the full check and merges seller replies |
| `extract.py` | Listing and reply extraction with Nemotron |
| `search.py` | Candidate search over the saved CPSC copy, with live CPSC fallback |
| `scope.py` | Recall scope extraction and quote verification |
| `matcher.py` | Plain-Python matching logic |
| `questions.py` | Seller question generation |
| `websearch.py` | Tavily context search |
| `build_snapshot.py` | Builds `recalls_snapshot.json` from the CPSC API |
| `test_matcher.py` | Unit tests for the matcher |

## Limitations

- Covers CPSC consumer product recalls only. Cars and car seats (NHTSA) are not included.
- The saved copy does not include recalls announced after its snapshot date.
- Candidate search uses simple keyword ranking, so listings without a brand or clear product type may miss relevant recalls.
- This is a hackathon prototype. Always confirm with the official recall notice and the manufacturer.

## License

MIT
