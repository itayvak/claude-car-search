---
name: calculate-car-score
description: Calculate a used car's 0-100 score from year, price, mileage, hand and horsepower. Use whenever a listing needs scoring or two cars need comparing numerically.
---

Run (Python, no dependencies):

```
python .claude/skills/calculate-car-score/scripts/score.py --year 2018 --price 38000 --mileage 90000 --hand 2 --hp 90
```

Output: JSON with `score` (average of factors) and per-factor `factors`. Report the score; don't recompute by hand.

Each factor is linear and clamped to 0-100:

| Factor  | 100 pts  | 0 pts     |
|---------|----------|-----------|
| year    | 2022     | 2010      |
| price   | ₪1,500   | ₪50,000   |
| mileage | 50,000km | 160,000km |
| hand    | 1st      | 6th       |
| hp      | 100 HP   | 45 HP     |

Ranges live in `RANGES` in `scripts/score.py`.
