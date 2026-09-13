#!/usr/bin/env python3
"""Compare raw and rendered HTML and apply the CG-002 four-condition gate."""
from __future__ import annotations
import argparse, json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

IMPORTANT = ("price", "availability", "spec", "contact", "hours", "shipping", "returns")
SSR_MARKERS = ("__NEXT_DATA__", "window.__NUXT__", "serverRendered", "prerender")
PATTERNS = {
    "price": r"(?:[$€£]\s?\d[\d,.]*|\b(?:price|cost)\b)", "availability": r"\b(?:in stock|out of stock|available)\b",
    "spec": r"\b(?:specification|dimensions|weight|materials?)\b", "contact": r"\b(?:contact|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})\b",
    "hours": r"\b(?:hours?|open(?:ing)?\s+(?:times?|hours?))\b", "shipping": r"\bshipping\b", "returns": r"\breturns?\b"
}

class Text(HTMLParser):
    def __init__(self) -> None: super().__init__(); self.bits: list[str] = []; self.hidden = 0
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs); self.hidden += int(tag in {"script", "style"} or "display:none" in (data.get("style") or "").replace(" ", "").lower() or "hidden" in data)
    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.hidden: self.hidden -= 1
    def handle_data(self, data: str) -> None:
        if not self.hidden: self.bits.append(data)

def visible_text(html: str) -> str:
    parser = Text(); parser.feed(html); return " ".join(parser.bits).lower()

def present_facts(html: str) -> list[str]:
    text = visible_text(html)
    return [name for name in IMPORTANT if re.search(PATTERNS[name], text, re.I)]

def client_rendered(raw_html: str) -> bool:
    """Conservative heuristic: an application shell, not ordinary static HTML."""
    lower=raw_html.lower()
    shell=bool(re.search(r'(?:id|class)=["\'][^"\']*(?:app|root)[^"\']*["\']',lower) or re.search(r'loading\s*(?:catalog|app|content|\.\.\.)',lower))
    return shell and not any(marker.lower() in lower for marker in SSR_MARKERS)

def classify(raw_html: str, rendered_html: str, equivalent_elsewhere: bool, url: str = "local") -> dict[str, object]:
    raw, rendered = set(present_facts(raw_html)), set(present_facts(rendered_html))
    missing = sorted(rendered - raw)
    conditions = {"important_missing": bool(missing), "present_after_render": bool(missing), "client_rendered": client_rendered(raw_html), "no_equivalent_elsewhere": not equivalent_elsewhere}
    if all(conditions.values()): severity = "high"
    elif conditions["important_missing"] and conditions["present_after_render"] and conditions["client_rendered"]: severity = "medium"
    elif conditions["important_missing"]: severity = "informational"
    else: severity = None
    result: dict[str, object] = {"check_id": "CG-002", "url": url, "raw_facts": sorted(raw), "rendered_facts": sorted(rendered), "missing_facts": missing, "conditions": conditions, "severity": severity}
    if severity: result["evidence"] = f"{len(missing)}/{len(IMPORTANT)} important fact types absent from raw HTML and present after render at {url}: {', '.join(missing)}"
    return result

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("raw_html", type=Path); parser.add_argument("rendered_html", type=Path); parser.add_argument("--equivalent-elsewhere", action="store_true"); parser.add_argument("--url", default="local")
    args = parser.parse_args(argv)
    result = classify(args.raw_html.read_text(encoding="utf-8"), args.rendered_html.read_text(encoding="utf-8"), args.equivalent_elsewhere, args.url)
    json.dump(result, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 1 if result["severity"] else 0

if __name__ == "__main__": raise SystemExit(main())
