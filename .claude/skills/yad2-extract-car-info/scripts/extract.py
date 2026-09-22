"""Extract a Yad2 vehicle listing as compact JSON (headless-capable).

Yad2 sits behind Radware bot protection: plain HTTP and default headless
Chromium are blocked. Real Chrome + normal UA + no automation flag passes.
Data comes from the page's embedded __NEXT_DATA__ JSON.

Env: YAD2_PROXY (e.g. http://user:pass@host:port) for cloud IPs that get captcha'd,
     YAD2_HEADED=1 to run headed (use under xvfb-run if a display is missing).
Exit codes: 0 ok, 2 blocked by bot protection, 3 listing data not found.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))
from yad2_browser import launch_page, wait_for_next_data


def normalize(url):
    url = url.strip()
    if re.fullmatch(r"[a-z0-9]{6,12}", url):
        url = f"https://www.yad2.co.il/vehicles/item/{url}"
    if not url.startswith("http"):
        url = "https://" + url
    return url


def fetch_next_data(url):
    with sync_playwright() as p:
        browser, page = launch_page(p)
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        raw, blocked = wait_for_next_data(page)
        browser.close()
    return raw, blocked


def find_item(next_data):
    for q in next_data["props"]["pageProps"]["dehydratedState"]["queries"]:
        if q["queryKey"][:2] == ["vehicles", "item"]:
            return q["state"]["data"]
    return None


def txt(d, k):
    v = d.get(k)
    return v.get("text") if isinstance(v, dict) else v


def summarize(d, url):
    vd = d.get("vehicleDates") or {}
    return {
        "url": url,
        "manufacturer": txt(d, "manufacturer"),
        "model": txt(d, "model"),
        "sub_model": txt(d, "subModel"),
        "gearbox": txt(d, "gearBox"),
        "color": txt(d, "color"),
        "year": vd.get("yearOfProduction"),
        "price": d.get("price"),  # None/0 = no price (teaser)
        "km": d.get("km"),
        "hand": (d.get("hand") or {}).get("id"),
        "hp": d.get("horsePower"),
        "description": (d.get("metaData") or {}).get("description") or "",
    }


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: extract.py <yad2 listing URL or token>")
    url = normalize(sys.argv[1])
    raw, blocked = fetch_next_data(url)
    if not raw:
        print(json.dumps({"error": "blocked_by_bot_protection" if blocked else "no_listing_data",
                          "url": url}, ensure_ascii=False))
        sys.exit(2 if blocked else 3)
    item = find_item(json.loads(raw))
    if not item:
        print(json.dumps({"error": "listing_not_found_in_page", "url": url}))
        sys.exit(3)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summarize(item, url), ensure_ascii=False))


if __name__ == "__main__":
    main()
