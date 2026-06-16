#!/usr/bin/env python3
"""Visible Dianping login helper that saves Playwright session cookies privately."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_ENV_FILE = Path.home() / ".codex" / "skills" / "dianping-explore" / ".env"
DEFAULT_URL = "https://www.dianping.com/"
COOKIE_ENV_NAME = "DIANPING_COOKIE"


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Assist Dianping visible login and save cookies")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--url", default=DEFAULT_URL)
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
        browser = playwright.chromium.launch(headless=False)
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

        print("[dianping-explore] A visible browser is open.")
        print("[dianping-explore] Complete Dianping login or verification in that browser.")
        input("[dianping-explore] Press Enter here after login/verification is complete...")

        cookies = context.cookies(
            [
                "https://www.dianping.com/",
                "https://m.dianping.com/",
                "https://mapi.dianping.com/",
            ]
        )
        cookie_header = to_cookie_header(cookies)
        marker = has_login_marker(cookies)
        context.close()
        browser.close()

    if not cookie_header:
        return emit(
            {
                "ok": False,
                "error": "No dianping.com cookies were found in the Playwright session.",
                "env_file": str(env_file),
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
            "message": "Saved Dianping cookies without printing their values.",
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
