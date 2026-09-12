#!/usr/bin/env python3
"""Measure whether a single sampled page answers each detected user intent end-to-end."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

INTENTS: dict[str, tuple[tuple[str, ...], ...]] = {
    "pricing": (("price", "pricing", "$", "cost"), ("plan", "buy", "purchase", "per month", "quote")),
    "what-is-it": (("what is", "our platform", "our service", "our product", "we make"), ("helps", "built for", "provides", "designed for")),
    "who-is-it-for": (("for teams", "for businesses", "for professionals", "for survey", "customers", "audience"), ("designed", "built", "use case", "need", "ideal")),
    "how-to-buy": (("buy", "purchase", "order", "get started", "subscribe"), ("cart", "checkout", "contact sales", "trial", "plan")),
    "support": (("support", "help", "contact", "documentation", "faq"), ("email", "hours", "guide", "submit", "ticket")),
}

class TextParser(HTMLParser):
    def __init__(self) -> None: super().__init__(); self.bits: list[str] = []; self.skip = 0
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}: self.skip += 1
    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip: self.skip -= 1
    def handle_data(self, data: str) -> None:
        if not self.skip: self.bits.append(data)

def text(html: str) -> str:
    parser = TextParser(); parser.feed(html); return " ".join(parser.bits).lower()

def analyse(pages: dict[str, str]) -> dict[str, object]:
    results: dict[str, object] = {}; findings: list[dict[str, object]] = []
    for intent, groups in INTENTS.items():
        matches: list[tuple[str, int]] = []
        for url, html in sorted(pages.items()):
            page_text = text(html)
            score = sum(any(term in page_text for term in group) for group in groups)
            if score: matches.append((url, score))
        complete = [url for url, score in matches if score == len(groups)]
        partial = [url for url, score in matches if 0 < score < len(groups)]
        status = "anchor" if complete else "smeared" if len(partial) >= 2 else "undetected"
        results[intent] = {"status": status, "anchor_pages": complete, "partial_pages": partial}
        if status == "smeared":
            findings.append({"check_id": "EF-005", "title": f"{intent} answer is smeared across thin pages", "severity": "medium", "chain_link": "understand", "impact_area": "discoverability", "evidence": f"{len(partial)}/{len(pages)} sampled pages partially answer {intent}; no page covers both required signal groups. Samples: {', '.join(partial[:2])}", "suggested_action": "Create one canonical anchor page that answers the detected intent end-to-end."})
    return {"intents": results, "findings": findings}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("html_dir", type=Path)
    args = parser.parse_args(argv)
    if not args.html_dir.is_dir(): print("usage error: html_dir must be a directory", file=sys.stderr); return 2
    pages = {path.relative_to(args.html_dir).as_posix(): path.read_text(encoding="utf-8") for path in sorted(args.html_dir.rglob("*.html"))}
    json.dump(analyse(pages), sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0
if __name__ == "__main__": raise SystemExit(main())
