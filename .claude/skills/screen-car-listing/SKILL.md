---
name: screen-car-listing
description: Full screening of one Yad2 listing via a sub-agent - extracts the car info, calculates its 0-100 score, runs a reliability check, and returns one simple JSON. Use when the user gives a yad2.co.il/vehicles/item link (or token) and wants it checked/screened, or when many listings need screening in parallel (one sub-agent each).
---

Input: a Yad2 listing URL or token.

Spawn ONE sub-agent (Agent tool, `general-purpose`, `model: "sonnet"`, run in foreground) with this prompt, substituting `<input>`:

> Screen this Yad2 listing: `<input>`. Work from the project root. Do these in order, using the project skills (Skill tool):
> 1. `yad2-extract-car-info` on the input. If it fails (exit 2/3) or `price` is null/0, return `{"error": "<reason>", "url": "<input>"}` and stop.
> 2. `calculate-car-score` with the extracted `year`, `price`, `km` (as mileage), `hand`, `hp`.
> 3. `car-reliability-check` with `manufacturer`, `model`, `year`, and the engine/gearbox from `sub_model`/`gearbox`.
> 4. Save the result: write the JSON below to a temp file in the scratchpad and run `python .claude/skills/screen-car-listing/scripts/save_csv.py < <file>`. It appends to `cars.csv` (skips duplicates by token; ignore its output).
>
> Return ONLY this JSON, no other text:
> ```
> {
>   "car": { <the extract JSON, unchanged> },
>   "score": <0-100 number>,
>   "score_factors": { <per-factor values from score script> },
>   "reliability_score": <1-10 number>,
>   "reliability_confidence": "high|med|low",
>   "reliability_summary": "<4-6 sentence summary of what the research concluded: overall verdict and why, the specific engine/gearbox findings, main known issues with typical km/cost, any conflicting evidence or thin data, and which sources it rests on>"
> }
> ```

Relay the sub-agent's JSON to the user as-is. Don't add commentary unless asked. For several listings, spawn one sub-agent per listing in a single message (parallel) and return a JSON array.
