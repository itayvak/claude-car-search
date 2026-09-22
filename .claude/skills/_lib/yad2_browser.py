"""Shared Playwright launch + __NEXT_DATA__ polling for Yad2 scripts.

Yad2 sits behind Radware bot protection: plain HTTP and default headless
Chromium are blocked. Real Chrome + normal UA + no automation flag passes.

Env: YAD2_PROXY (e.g. http://user:pass@host:port) for cloud IPs that get captcha'd,
     YAD2_HEADED=1 to run headed (use under xvfb-run if a display is missing).
"""
import os

from playwright.sync_api import Error as PlaywrightError

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
ARGS = ["--disable-blink-features=AutomationControlled", "--no-sandbox"]


def launch_page(p):
    """Launch a bot-evasion browser + context + page. Returns (browser, page)."""
    opts = dict(headless=not os.environ.get("YAD2_HEADED"), args=ARGS,
                ignore_default_args=["--enable-automation"])
    if os.environ.get("YAD2_PROXY"):
        opts["proxy"] = {"server": os.environ["YAD2_PROXY"]}
    try:
        browser = p.chromium.launch(channel="chrome", **opts)
    except Exception:  # Chrome not installed: fall back to bundled Chromium
        browser = p.chromium.launch(**opts)
    ctx = browser.new_context(locale="he-IL", timezone_id="Asia/Jerusalem",
                              user_agent=UA, viewport={"width": 1366, "height": 850})
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    return browser, ctx.new_page()


def wait_for_next_data(page, tries=10, interval_ms=2500):
    """Poll for the page's __NEXT_DATA__ JSON, retrying past Radware interstitials.

    Returns (raw_json_str_or_None, blocked_bool).
    """
    raw = None
    blocked = False
    for _ in range(tries):
        page.wait_for_timeout(interval_ms)
        try:
            blocked = "Radware" in page.title()
            if blocked:
                continue
            raw = page.evaluate("document.getElementById('__NEXT_DATA__')?.textContent")
        except PlaywrightError:
            # mid-navigation race (redirect/challenge reload tore down the JS context) - retry
            continue
        if raw:
            break
    return raw, blocked
