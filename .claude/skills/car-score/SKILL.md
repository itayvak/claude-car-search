---
name: car-score
description: Calculate a used car's 0-100 score from year, price, mileage and hand. Use whenever a listing needs scoring or two cars need comparing numerically.
---

Run (Python, no dependencies):

```
python .claude/skills/car-score/scripts/score.py --year 2018 --price 38000 --mileage 90000 --hand 2
```

Output: JSON with `score` (average of factors) and per-factor `factors`. Report the score; don't recompute by hand.

Each factor is linear and clamped to 0-100:

| Factor  | 100 pts  | 0 pts     |
|---------|----------|-----------|
| year    | 2022     | 2010      |
| price   | ₪1,500   | ₪50,000   |
| mileage | 50,000km | 160,000km |
| hand    | 1st      | 6th       |

Horsepower is not scored yet (CLAUDE.md lists it as a factor; ranges pending).
Ranges live in `RANGES` in `scripts/score.py`.
