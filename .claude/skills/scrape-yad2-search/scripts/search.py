"""Sweep Yad2's used-car search results as compact candidate JSON (headless-capable).

Filters apply via the search URL's own query params (price=min-max, year=min-max,
page=N) - confirmed against the actively-maintained yad2-scraper PyPI package's
source, which uses the same params over plain HTTP. Results come from the page's
embedded __NEXT_DATA__ JSON, same mechanism yad2-extract-car-info uses for a
single item page. Unlike an item page, the feed query's data is split across
several category keys (platinum/boost/solo/commercial/private, etc., seen live -
not documented anywhere) rather than one "ads" array, so every dict-valued array
in the feed data is flattened together.

There is no known query param for gearbox, and the feed's per-item data never
includes km/gearBox at all (both are always null here - only the item-detail
page has them). So gearbox can't be screened until each candidate goes through
full extraction; the calling skill's screen-car-listing step enforces it there.

Env: YAD2_PROXY (e.g. http://user:pass@host:port) for cloud IPs that get captcha'd,
     YAD2_HEADED=1 to run headed (use under xvfb-run if a display is missing).
Exit codes: 0 ok, 2 blocked by bot protection, 3 no results found at all.
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))
from yad2_browser import launch_page, wait_for_next_data

SEARCH_URL = "https://www.yad2.co.il/vehicles/cars"

FEED_JS = """
() => {
    const nd = JSON.parse(document.getElementById('__NEXT_DATA__')?.textContent || 'null');
    if (!nd) return {method: 'none'};
    const queries = nd.props?.pageProps?.dehydratedState?.queries || [];
    const feedQ = queries.find(q => q.queryKey?.[0] === 'feed' && q.queryKey?.[1] === 'vehicles');
    if (!feedQ || !feedQ.state?.data) return {method: 'no_feed_query'};
    const d = feedQ.state.data;
    const ads = [];
    for (const v of Object.values(d)) {
        if (!Array.isArray(v)) continue;
        for (const item of v) {
            if (!item || typeof item !== 'object' || !item.token) continue;
            ads.push({
                token: item.token,
                adType: item.adType,
                manufacturer: item.manufacturer?.textEng || item.manufacturer?.text,
                model: item.model?.textEng || item.model?.text,
                subModel: item.subModel?.text,
                year: item.vehicleDates?.yearOfProduction,
                price: item.price,
                km: item.km,
                hand: item.hand?.text,
                gearBox: item.gearBox?.text,
                city: item.address?.city?.text,
                agencyName: item.customer?.agencyName,
                createdAt: item.dates?.createdAt,
            });
        }
    }
    return {method: 'next_data', totalPages: d.pagination?.totalPages, ads};
}
"""

CARD_FALLBACK_JS = """
() => {
    const links = Array.from(document.querySelectorAll('a[href*="/vehicles/item/"]'));
    const seen = new Set();
    const ads = [];
    for (const a of links) {
        const m = a.getAttribute('href').match(/\\/vehicles\\/item\\/([a-z0-9]+)/);
        if (!m || seen.has(m[1])) continue;
        seen.add(m[1]);
        ads.push({token: m[1], cardText: (a.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 200)});
    }
    return ads;
}
"""


def build_url(max_price, min_year, page_num, manufacturer=None, model=None):
    params = []
    if manufacturer is not None:
        params.append(f"manufacturer={manufacturer}")
    if model is not None:
        params.append(f"model={model}")
    if max_price is not None:
        params.append(f"price=0-{max_price}")
    if min_year is not None:
        params.append(f"year={min_year}-{2100}")
    if page_num > 1:
        params.append(f"page={page_num}")
    qs = "&".join(params)
    return f"{SEARCH_URL}?{qs}" if qs else SEARCH_URL


def load_feed(page, url, attempts=2):
    """Navigate to url and read the feed, retrying once on a non-blocked empty load."""
    for attempt in range(1, attempts + 1):
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        raw, blocked = wait_for_next_data(page)
        if blocked:
            return None, True
        if not raw:
            continue  # transient: page didn't finish hydrating in time - retry
        result = page.evaluate(FEED_JS)
        if result.get("method") == "next_data":
            return result, False
        if attempt == attempts:
            cards = page.evaluate(CARD_FALLBACK_JS)
            if cards:
                return {"method": "card_fallback", "totalPages": None, "ads": cards}, False
    return None, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-price", type=int, default=None)
    ap.add_argument("--min-year", type=int, default=None)
    ap.add_argument("--max-pages", type=int, default=5)
    ap.add_argument("--manufacturer", type=int, default=None, help="Yad2 manufacturer id")
    ap.add_argument("--model", type=int, default=None, help="Yad2 model id")
    args = ap.parse_args()

    candidates = []
    pages_scanned = 0
    extraction_method = None
    with sync_playwright() as p:
        browser, page = launch_page(p)

        for page_num in range(1, args.max_pages + 1):
            url = build_url(args.max_price, args.min_year, page_num, args.manufacturer, args.model)
            feed, blocked = load_feed(page, url)
            if blocked:
                print(json.dumps({"error": "blocked_by_bot_protection"}, ensure_ascii=False))
                browser.close()
                sys.exit(2)
            if not feed or not feed.get("ads"):
                break
            extraction_method = feed.get("method")
            candidates.extend(feed["ads"])
            pages_scanned += 1
            total_pages = feed.get("totalPages")
            if extraction_method != "next_data" or (total_pages and pages_scanned >= total_pages):
                break

        browser.close()

    if pages_scanned == 0:
        print(json.dumps({"error": "no_results_found"}, ensure_ascii=False))
        sys.exit(3)

    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({
        "pages_scanned": pages_scanned,
        "extraction_method": extraction_method,
        "candidates": candidates,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
