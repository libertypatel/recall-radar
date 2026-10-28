import json
from datetime import date
from search import cpsc_query, SourceUnavailable

SNAPSHOT_PATH = "recalls_snapshot.json"
START_YEAR = 2020


def month_ranges():
    """List (start, end) date strings for every month from START_YEAR through this month."""
    today = date.today()
    ranges = []
    year, month = START_YEAR, 1
    while (year, month) <= (today.year, today.month):
        next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
        start = date(year, month, 1).isoformat()
        end = date(next_year, next_month, 1).isoformat()
        ranges.append((start, end))
        year, month = next_year, next_month
    return ranges


if __name__ == "__main__":
    found = {}
    failed = []
    for start, end in month_ranges():
        try:
            for recall in cpsc_query(RecallDateStart=start, RecallDateEnd=end):
                found[recall["RecallID"]] = recall
        except SourceUnavailable:
            failed.append(start[:7])
            print("Failed:", start[:7])

    snapshot = {
        "saved_on": date.today().isoformat(),
        "count": len(found),
        "failed_months": failed,
        "recalls": list(found.values()),
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f)
    print(f"Saved {len(found)} recalls. Failed months: {failed or 'none'}")