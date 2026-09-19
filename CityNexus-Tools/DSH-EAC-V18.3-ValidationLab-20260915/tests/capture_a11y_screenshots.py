#!/usr/bin/env python3
"""Capture the four required A11y viewports into evidence/screenshots/.

Requires:
  - isolated backend up on :8022  (tests/_run_backend_foreground.py)
  - frontend dev server up on :5173 (cd source-snapshot/frontend && npm run dev)
  - a browser automation backend available to the environment
    (playwright / smooth-browser). This script shells out to `playwright`
    CLI if installed; otherwise it documents the manual steps.

This is a capture *harness* only -- it does not modify the product.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "evidence", "screenshots")
VIEWPORTS = [
    ("desktop_1440x900", 1440, 900),
    ("desktop_1280x720", 1280, 720),
    ("mobile_390x844", 390, 844),
    ("mobile_430x932", 430, 932),
]
FRONTEND_URL = "http://127.0.0.1:5173/"


def capture_with_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, w, h in VIEWPORTS:
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(FRONTEND_URL, wait_until="networkidle")
            page.screenshot(path=os.path.join(OUT, f"{name}.png"))
            print(f"captured {name}.png ({w}x{h})")
        browser.close()
    return True


def capture_with_cli():
    """Fallback: drive the playwright CLI if the python package is absent."""
    os.makedirs(OUT, exist_ok=True)
    for name, w, h in VIEWPORTS:
        out = os.path.join(OUT, f"{name}.png")
        cmd = [
            "playwright", "open", FRONTEND_URL,
            "--viewport-size", f"{w},{h}",
            "--save-trace", out,
        ]
        try:
            subprocess.run(cmd, check=False, timeout=60)
            print(f"(cli) {name}.png requested ({w}x{h})")
        except FileNotFoundError:
            return False
    return True


if __name__ == "__main__":
    if not capture_with_playwright():
        if not capture_with_cli():
            print(
                "No browser automation available in this environment.\n"
                "Manual capture: open the :5173 frontend at each viewport and "
                "save a PNG into evidence/screenshots/ (see screenshots/README.md).",
                file=sys.stderr,
            )
            sys.exit(2)
