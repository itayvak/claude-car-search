"""Append a screening result (JSON on stdin) to cars.csv in the project root, skipping duplicates by Yad2 token."""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[4] / "cars.csv"
COLUMNS = [
    "date_screened", "token", "url", "manufacturer", "model", "sub_model", "year", "price", "km", "hand", "hp",
    "gearbox", "color", "score", "reliability_score", "reliability_confidence", "reliability_summary", "description",
]


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    data = json.load(sys.stdin)
    if "error" in data:
        print("skipped: error result")
        return
    car = data["car"]
    token = car["url"].rstrip("/").split("/")[-1].split("?")[0]
    rows = []
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    if any(r["token"] == token for r in rows):
        print(f"duplicate: {token} already in {CSV_PATH.name}")
        return
    row = {c: car.get(c, "") for c in COLUMNS}
    row.update(
        date_screened=datetime.now().strftime("%Y-%m-%d %H:%M"),
        token=token,
        score=data["score"],
        reliability_score=data["reliability_score"],
        reliability_confidence=data["reliability_confidence"],
        reliability_summary=data["reliability_summary"],
        description=" ".join((car.get("description") or "").split()),
    )
    rows.append(row)
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:  # BOM so Excel reads Hebrew
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"saved: {token}")


main()
