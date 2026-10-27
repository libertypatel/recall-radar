import json
from datetime import date
from search import cpsc_query

SNAPSHOT_PATH = "recalls_snapshot.json"
START_DATE = "2020-01-01"


if __name__ == "__main__":
    recalls = cpsc_query(RecallDateStart=START_DATE)
    snapshot = {
        "saved_on": date.today().isoformat(),
        "recall_date_start": START_DATE,
        "count": len(recalls),
        "recalls": recalls,
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f)
    print(f"Saved {len(recalls)} recalls since {START_DATE} to {SNAPSHOT_PATH}")