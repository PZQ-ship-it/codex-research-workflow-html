#!/usr/bin/env python3
"""Visible Dianping login helper that saves Playwright session cookies privately."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_ENV_FILE = Path.home() / ".codex" / "skills" / "dianping-explore" / ".env"
DEFAULT_URL = "https://www.dianping.com/"
COOKIE_ENV_NAME = "DIANPING_COOKIE"
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_POLL_SECONDS = 2.0
SAVE_FLAG = "__dianpingExploreSaveCookies"


def emit(payload: Dict[str, object], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def quote_env_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_env_value(env_file: Path, key: str, value: str) -> None:
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    new_line = f"{key}={quote_env_value(value)}"
    updated: List[str] = []
    replaced = False
    for line in lines:
        if pattern.match(line.lstrip("\ufeff")):
            updated.append(new_line)
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(new_line)

    env_file.write_text("\n".join(updated) + "\n", encoding="utf-8")


def domain_matches(cookie: Dict[str, object]) -> bool:
    domain = str(cookie.get("domain", "")).lower()
    return "dianping.com" in domain


def to_cookie_header(cookies: Iterable[Dict[str, object]]) -> str:
    pairs = []
    seen = set()
    for cookie in cookies:
        if not domain_matches(cookie):
            continue
        name = str(cookie.get("name", "")).strip()
        value = str(cookie.get("value", ""))
        if not name or (name, value) in seen:
            continue
        seen.add((name, value))
        pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def has_login_marker(cookies: Iterable[Dict[str, object]]) -> bool:
    markers = {"dper", "dplet", "ua", "ctu"}
    names = {str(cookie.get("name", "")).lower() for cookie in cookies if domain_matches(cookie)}
    return bool(markers & names)


def inject_save_panel(
    page: object,
    cookie_count: int,
    marker: bool,
    allow_unverified_save: bool,
) -> None:
    try:
        page.evaluate(
            """
            ({ flag, cookieCount, marker, allowUnverifiedSave }) => {
              const id = "dianping-explore-save-panel";
              let panel = document.getElementById(id);
              if (!panel) {
                panel = document.createElement("div");
                panel.id = id;
                panel.style.cssText = [
                  "position:fixed",
                  "z-index:2147483647",
                  "right:16px",
                  "bottom:16px",
                  "max-width:360px",
                  "padding:12px",
                  "background:#111827",
                  "color:white",
                  "font:13px/1.4 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif",
                  "border-radius:8px",
                  "box-shadow:0 10px 30px rgba(0,0,0,.28)"
                ].join(";");
                const title = document.createElement("div");
                title.textContent = "Dianping Explore login helper";
                title.style.cssText = "font-weight:700;margin-bottom:6px;";
                const body = document.createElement("div");
                body.dataset.role = "body";
                body.style.cssText = "margin-bottom:10px;";
                const button = document.createElement("button");
                button.textContent = "Save Dianping cookies";
                button.style.cssText = [
                  "border:0",
                  "border-radius:6px",
                  "padding:7px 10px",
                  "cursor:pointer",
                  "background:#f97316",
                  "color:white",
                  "font-weight:600"
                ].join(";");
                button.addEventListener("click", () => {
                  if (button.disabled) return;
                  window[flag] = true;
                  button.textContent = "Saving...";
                  button.disabled = true;
                });
                panel.append(title, body, button);
                document.documentElement.appendChild(panel);
              }
              const body = panel.querySelector("[data-role='body']");
              const button = panel.querySelector("button");
              if (body) {
                body.textContent = marker
                  ? "Login cookies detected. Saving automatically..."
                  : allowUnverifiedSave
                    ? `Complete login/CAPTCHA/MFA here. Cookies seen: ${cookieCount}. If you are logged in, click Save.`
                    : `Complete login/CAPTCHA/MFA here. Cookies seen: ${cookieCount}. Waiting for login markers.`;
              }
              if (button && !marker) {
                button.disabled = !allowUnverifiedSave;
                button.style.opacity = allowUnverifiedSave ? "1" : ".55";
                button.title = allowUnverifiedSave
                  ? "Save the current Dianping cookies"
                  : "Disabled until login markers are detected; rerun with --allow-unverified-save only if the site changed its login cookies.";
              }
            }
            """,
            {
                "flag": SAVE_FLAG,
                "cookieCount": cookie_count,
                "marker": marker,
                "allowUnverifiedSave": allow_unverified_save,
            },
        )
    except Exception:
        return


def browser_save_requested(pages: Iterable[object]) -> bool:
    for page in pages:
        try:
            if page.evaluate(f"() => window.{SAVE_FLAG} === true"):
                return True
        except Exception:
            continue
    return False


def live_pages(context: object) -> List[object]:
    pages = []
    for page in list(context.pages):
        try:
            if not page.is_closed():
                pages.append(page)
        except Exception:
            continue
    return pages


def wait_for_cookie_capture(
    context: object,
    timeout_seconds: int,
    poll_seconds: float,
    allow_unverified_save: bool,
) -> tuple[List[Dict[str, object]], str]:
    cookie_urls = [
        "https://www.dianping.com/",
        "https://m.dianping.com/",
        "https://mapi.dianping.com/",
    ]
    deadline = time.monotonic() + timeout_seconds
    last_cookies: List[Dict[str, object]] = []

    while time.monotonic() < deadline:
        pages = live_pages(context)
        cookies = context.cookies(cookie_urls)
        last_cookies = cookies
        cookie_count = len([c for c in cookies if domain_matches(c)])
        marker = has_login_marker(cookies)

        for page in pages:
            inject_save_panel(page, cookie_count, marker, allow_unverified_save)

        if marker:
            return cookies, "login-marker"
        if (
            browser_save_requested(pages)
            and allow_unverified_save
            and to_cookie_header(cookies)
        ):
            return cookies, "browser-save-button"
        if browser_save_requested(pages) and to_cookie_header(cookies):
            return cookies, "browser-save-without-login-marker"
        time.sleep(max(poll_seconds, 0.25))

    return last_cookies, "timeout"


def main() -> int:
    parser = argparse.ArgumentParser(description="Assist Dianping visible login and save cookies")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--headless", action="store_true", help="test mode only; default is a visible browser")
    parser.add_argument(
        "--allow-unverified-save",
        action="store_true",
        help="escape hatch only; save cookies after browser-side confirmation even without known login markers",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env_file = Path(args.env_file).expanduser().resolve()
    if args.dry_run:
        return emit(
            {
                "ok": True,
                "dry_run": True,
                "url": args.url,
                "env_file": str(env_file),
                "cookie_env": COOKIE_ENV_NAME,
                "mode": "visible-playwright-login",
                "timeout_seconds": args.timeout_seconds,
                "poll_seconds": args.poll_seconds,
                "headless": args.headless,
                "stdin_required": False,
                "requires_login_marker": not args.allow_unverified_save,
            }
        )

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        return emit(
            {
                "ok": False,
                "error": "Playwright is not available in the selected Python environment.",
                "detail": str(exc),
            },
            1,
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        context = browser.new_context(
            locale="zh-CN",
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/144.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded", timeout=30000)

        if args.headless:
            print("[dianping-explore] Headless test mode is running; no login UI is visible.")
        else:
            print("[dianping-explore] A visible browser is open.")
            print("[dianping-explore] Complete Dianping login or verification in that browser.")
        print(
            "[dianping-explore] No terminal input is required. Cookies will be saved automatically after login markers appear; if needed, click the in-browser Save button.",
            flush=True,
        )
        cookies, capture_reason = wait_for_cookie_capture(
            context,
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
            allow_unverified_save=args.allow_unverified_save,
        )
        cookie_header = to_cookie_header(cookies)
        marker = has_login_marker(cookies)
        context.close()
        browser.close()

    if not cookie_header:
        return emit(
            {
                "ok": False,
                "error": "No dianping.com cookies were captured before the helper stopped.",
                "capture_reason": capture_reason,
                "env_file": str(env_file),
            },
            1,
        )
    if not marker and not args.allow_unverified_save:
        return emit(
            {
                "ok": False,
                "error": "Dianping cookies were captured, but no likely login marker was found; not saving unverified cookies.",
                "capture_reason": capture_reason,
                "env_file": str(env_file),
                "cookies_seen_count": len([c for c in cookies if domain_matches(c)]),
            },
            1,
        )

    set_env_value(env_file, COOKIE_ENV_NAME, cookie_header)
    return emit(
        {
            "ok": True,
            "env_file": str(env_file),
            "cookie_env": COOKIE_ENV_NAME,
            "cookies_saved_count": len([c for c in cookies if domain_matches(c)]),
            "has_likely_login_cookie": marker,
            "capture_reason": capture_reason,
            "message": "Saved Dianping cookies without printing their values.",
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
