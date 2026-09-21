"""Car score (0-100): average of per-factor linear scores, each clamped to 0-100."""
import argparse
import json

# factor: (value giving 100 points, value giving 0 points)
RANGES = {
    "year": (2022, 2010),
    "price": (1_500, 50_000),      # ILS
    "mileage": (50_000, 160_000),  # km
    "hand": (1, 6),
    "hp": (100, 45),
}


def factor_score(name, value):
    best, worst = RANGES[name]
    pts = (value - worst) / (best - worst) * 100
    return max(0.0, min(100.0, pts))


def car_score(**values):
    scores = {k: round(factor_score(k, v), 1) for k, v in values.items()}
    return round(sum(scores.values()) / len(scores), 1), scores


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--price", type=float, required=True, help="ILS")
    ap.add_argument("--mileage", type=float, required=True, help="km")
    ap.add_argument("--hand", type=int, required=True)
    ap.add_argument("--hp", type=float, required=True, help="horsepower")
    a = ap.parse_args()
    total, parts = car_score(year=a.year, price=a.price, mileage=a.mileage, hand=a.hand, hp=a.hp)
    print(json.dumps({"score": total, "factors": parts}))
