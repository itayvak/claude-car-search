---
name: screen-car-listing
description: Full screening of one Yad2 listing via a sub-agent - extracts the car info, calculates its 0-100 score, runs a reliability check, and returns one simple JSON. Use when the user gives a yad2.co.il/vehicles/item link (or token) and wants it checked/screened, or when many listings need screening in parallel (one sub-agent each).
---

Input: a Yad2 listing URL or token.

The car database is the "Car Search — Database & Display" Claude Doc: `https://claude.ai/artifact/Mw9SDU8jNfZKTLJv5XmB69` (Cars tab = the table, Notes tab = per-car reliability write-up + description, keyed by token). Sub-agents only screen; only the top-level agent (you, running this skill) writes to the doc, to avoid concurrent-write races when several listings are screened in parallel.

Spawn ONE sub-agent (Agent tool, `general-purpose`, `model: "sonnet"`, run in foreground) with this prompt, substituting `<input>`:

> Screen this Yad2 listing: `<input>`. Work from the project root. Do these in order, using the project skills (Skill tool):
> 1. `yad2-extract-car-info` on the input. If it fails (exit 2/3) or `price` is null/0, return `{"error": "<reason>", "url": "<input>"}` and stop. If `gearbox` indicates manual transmission (not automatic), return `{"error": "manual_transmission", "url": "<input>"}` and stop - Itay holds no manual licence, this is a hard rule.
> 2. `calculate-car-score` with the extracted `year`, `price`, `km` (as mileage), `hand`, `hp`.
> 3. `car-reliability-check` with `manufacturer`, `model`, `year`, and the engine/gearbox from `sub_model`/`gearbox`.
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

For each non-error result, derive `token` from the URL (last path segment, stripped of query string). Before writing, search the Notes tab for that token (`read` with `payload:{"kind":"search","text":"<token>"}` on the Notes body) - a hit means it's already in the database, skip it (note as duplicate). Otherwise append it:
- Cars tab table: `insert` a row `"side":"end"` on the table id, cells in column order `Car | Year | Price | Km | Hand | HP | Score | Reliability | Status | Link` - `Car` = `"<manufacturer> <model> (<first word(s) of sub_model>)"`, `Reliability` = `"<reliability_score>/10 (<reliability_confidence>)"`, `Status` = empty, `Link` = `[Yad2](<url>)`.
- Notes tab body: `insert` `"side":"end"` on the root, markdown `## <manufacturer> <model> (<trim>) — <year> — <token>\n\nScreened <today, YYYY-MM-DD> · Sub-model: <sub_model> · Gearbox: <gearbox> · Color: <color>\n\n**Reliability:** <reliability_summary>\n\n**Description:** <car.description>`.

Several listings screened together: collect ALL sub-agent results first, THEN do the doc writes sequentially yourself (one append per car, in order) - never let sub-agents write the doc directly.

Relay the sub-agents' JSON to the user as-is. Don't add commentary unless asked. For several listings, spawn one sub-agent per listing in a single message (parallel) and return a JSON array.
