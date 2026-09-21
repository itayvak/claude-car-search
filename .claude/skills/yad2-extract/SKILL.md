---
name: yad2-extract
description: Extract a Yad2 vehicle listing (URL or token) into structured JSON - price, year, km, hand, hp, gearbox, engine, dealer, description. Use whenever the user gives a yad2.co.il/vehicles/item link or asks to check/screen a listing.
---

```
python .claude/skills/yad2-extract/scripts/extract.py <url-or-token>
```

Outputs one JSON line (UTF-8, Hebrew values). Feed `year`, `price`, `km`, `hand`, `hp` to the `car-score` skill.

**Why a browser:** Yad2 is behind Radware bot protection. Plain HTTP and default headless Chromium get blocked. The script uses Playwright with real Chrome (falls back to bundled Chromium), a normal UA and the automation flag removed, then reads the page's embedded `__NEXT_DATA__` JSON.

**Setup (cloud/CI):** `pip install playwright && playwright install --with-deps chrome`.

**Failures:**
- Exit 2 `blocked_by_bot_protection`: datacenter IPs may get a captcha. Set `YAD2_PROXY` (residential/Israeli proxy) or `YAD2_HEADED=1` under `xvfb-run`.
- Exit 3: no listing data (expired/removed listing).

**Reading the output:** `price` None/0 means a teaser with no real price; `ad_type: commercial` = dealer; `prev_owner_type` shows e.g. leasing history. Check `description` for financing/lease-only terms before trusting `price`. `fuel_km_per_l` is km per litre.
