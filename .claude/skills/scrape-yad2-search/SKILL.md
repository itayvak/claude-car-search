---
name: scrape-yad2-search
description: Sweep Yad2's used-car search results for listings matching Itay's criteria, rather than checking a single link he already has. Applies budget/year filters via the search URL, screens results for relevance, and runs the screen-car-listing skill (one sub-agent per candidate, in parallel) to extract, score, reliability-check and save each relevant new car to cars.csv. Trigger on things like "scan Yad2 for cars", "sweep Yad2 for automatics under budget", "go find some options on Yad2 and add anything good". For a single pasted listing link, use screen-car-listing directly instead.
---

# Yad2 search sweep into the car database

Run the steps below in order, at the top level (not inside a sub-agent).

## 1. Resolve criteria

Hard filters, applied via the search URL, always:
- price ≤ ₪45,000 (CLAUDE.md budget)
- year ≥ 2010 (efficiency cutoff matching `calculate-car-score`'s own range floor - cars older than this score near 0 anyway, not worth spending a deep-extraction sub-agent on)

There is no reliable Yad2 URL param for gearbox or mileage at the search-results level (see step 2's caveat), so those aren't filtered here - gearbox is enforced later, when `screen-car-listing` actually extracts each candidate (it now skips manual transmission there).

Any manufacturer/model or other criteria Itay states this turn are additional constraints to apply during the relevance screen (step 4), since there's no URL param for them either. No brand or segment is ever excluded (per CLAUDE.md).

State the resolved criteria back in one line before running.

## 2. Run the search script

```
python .claude/skills/scrape-yad2-search/scripts/search.py --max-price 45000 --min-year 2010 --max-pages 5
```

Outputs one JSON object: `{"pages_scanned": N, "extraction_method": "next_data"|"card_fallback", "candidates": [...]}`. Each candidate has `token, adType, manufacturer, model, subModel, year, price, hand, city, agencyName` plus `km` and `gearBox`, which are **always null in this feed** (Yad2's search-results payload doesn't include them - only the per-listing item page does, which is exactly what `screen-car-listing` extracts next). Don't treat a null `km`/`gearBox` as a mismatch.

Exit codes: 2 = blocked by bot protection (retry once; if it persists, report it and stop rather than looping), 3 = no results at all (criteria may be too narrow, or the page failed to load - report and stop).

`--max-pages` defaults to 5 (~100-200 candidates, ~40 ads/page). Go higher only if Itay asks for a deeper sweep; report in step 8 how many pages were scanned and whether more were likely available (`pages_scanned == max_pages` and the last page was still full).

## 3. Cheap screen (no sub-agent, filtering the JSON in-conversation)

From the candidates array:
- Drop any with no/teaser price (null, 0, or below ~₪8,000 - lease/financing teaser, same convention `screen-car-listing` already uses for a missing price).
- If Itay stated extra criteria this turn (manufacturer/model/etc.) not expressible as a URL param, drop anything that clearly doesn't match. Don't drop on segment/body-type ambiguity - carry it through and let it get flagged in the final report instead of guessing it away.
- Don't drop on `km` or `gearBox` - they're not present in this data (see step 2).

## 4. Dedup against the database

Read `cars.csv` (if it exists), collect existing `token` values, drop any survivor whose token is already present.

## 5. Cap deep extraction

Cap the remaining candidates at 20 for this run unless Itay asked for more. If more relevant candidates remain, say so in the report rather than truncating silently.

## 6. Deep screen

For the capped list, follow `screen-car-listing`'s own documented pattern: one `Agent` tool call per listing URL (`https://www.yad2.co.il/vehicles/item/<token>`), all batched into a single message (parallel). It extracts, checks gearbox (skips manual transmission - `{"error": "manual_transmission", ...}`), scores, runs the reliability check, and saves to `cars.csv` itself. Use only this repo's skills (`yad2-extract-car-info`, `calculate-car-score`, `car-reliability-check`, `screen-car-listing`) - never a global/plugin skill.

## 7. Commit once

After all sub-agents return, `git add cars.csv`, one commit with today's date/time as the message (per CLAUDE.md), then push. One commit for the whole sweep, not one per listing, since sub-agents write `cars.csv` concurrently and per-listing commits would race/spam.

## 8. Report

Always close with a concrete summary:
- Resolved criteria (from step 1).
- Pages scanned, candidates found → survived cheap screen → already-in-db skipped → deep-extracted.
- A table of newly added cars (manufacturer / model / year / price / km / score / url).
- Anything skipped during deep screening (manual transmission, extraction errors) with the one-line reason `screen-car-listing` gave.
- Whether the page cap or the extraction cap was hit, and whether more candidates are likely still unscanned.
