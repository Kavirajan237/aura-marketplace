#!/usr/bin/env python3
"""Structural entity ambiguity analysis; it never performs a name search."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

COMMON_NAMES = frozenset({"apple", "delta", "focus", "orbit", "square", "target", "signal", "northstar", "sage", "union", "mercury", "atlas", "summit"})


def json_ld_same_as(html: str) -> bool:
    """Recognise sameAs structurally, including an empty list as absent."""
    for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if isinstance(item, dict) and item.get("sameAs"):
                return True
    return False


def assess(name: str | None, one_liner: str | None, html_pages: dict[str, str]) -> dict[str, object]:
    normalized = (name or "").strip().lower()
    words = re.findall(r"[a-z]+", normalized)
    common_name = len(words) == 1 and normalized in COMMON_NAMES
    has_same_as = any(json_ld_same_as(html) for html in html_pages.values())
    # A qualifier is a concrete descriptor beyond simply repeating the name.
    qualifier = bool(one_liner and len(re.findall(r"[A-Za-z0-9]+", one_liner)) >= 5 and normalized not in (one_liner or "").strip().lower())
    signals = {"common_word_or_phrase": common_name, "authoritative_sameAs_present": has_same_as, "distinguishing_qualifier_present": qualifier}
    risk_count = int(common_name) + int(not has_same_as) + int(not qualifier)
    risk = "high" if risk_count == 3 else "medium" if risk_count == 2 else "low"
    return {"name": name, "risk": risk, "signals": signals, "evidence_pages": sorted(html_pages)}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True); parser.add_argument("--one-liner", default="")
    parser.add_argument("html_files", type=Path, nargs="+")
    args = parser.parse_args(argv)
    try:
        pages = {path.as_posix(): path.read_text(encoding="utf-8") for path in sorted(args.html_files)}
    except OSError as exc:
        print(f"usage error: {exc}", file=sys.stderr); return 2
    json.dump(assess(args.name, args.one_liner or None, pages), sys.stdout, sort_keys=True); sys.stdout.write("\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
