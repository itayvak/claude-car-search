---
name: car-reliability-check
description: Rate a used car model's reliability 1-10 by searching the web across multiple independent sources. Input is manufacturer + model, optionally year, engine and gearbox. Use when a listing or shortlist needs a reliability/known-issues check.
---

**Input:** manufacturer + model. Add year/generation, engine and gearbox when known (e.g. from `yad2-extract-car-info`'s `sub_model`). Reliability varies by engine+gearbox combo and model year, so search for the specific combo, not just the brand.

**Search at least 4 of these fronts** (WebSearch/WebFetch; Israel market matters):
1. Reliability surveys/rankings: Consumer Reports, J.D. Power, TÜV/ADAC, Which?, Auto Express, TrueDelta, Israeli reliability surveys.
2. Recalls and complaints: NHTSA, CarComplaints.com, Israeli Ministry of Transport recalls.
3. Owner forums/Reddit: "[model] [engine/gearbox] problems", high-mileage reports.
4. Mechanic/repair sources: common failures, repair cost, at ~100k+ km.
5. Israeli sources: Israeli car sites/forums (e.g. Auto.co.il, Facebook/Tapuz threads), importer service quality and parts availability.

Skip low-quality sources (SEO listicles, dealer ads). Prefer sources agreeing with each other; note conflicts.

**Scoring rubric (1-10):**
- 9-10: consistently top-rated across sources, no notable systemic faults
- 7-8: above average, minor recurring issues
- 5-6: average, or mixed/conflicting evidence
- 3-4: known systemic faults (e.g. transmission, engine design flaw) or many complaints
- 1-2: severe or widespread failures, costly recalls
Weigh the specific engine+gearbox and years over the brand's general reputation. If the combo has a known design flaw, cap at 5. If evidence is thin, say so and lower confidence rather than guessing high.

**Output (concise):**
```
Score: X/10 (confidence: high/med/low)
Model: <manufacturer model, years, engine, gearbox>
Why: <1-2 lines>
Known issues: <bullets, with typical km/cost if found>
Sources: <3-6 names/URLs>
```
