#!/usr/bin/env python3
"""Read local HTML artifacts and emit the entity/fact partial AURA Brand Twin patch."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0, str(SCRIPT_DIR))
import anchor_page  # noqa: E402
import entity_disambiguation  # noqa: E402

FACT_PATTERNS = {"founded": re.compile(r"\b(?:founded|established|since)\s+(?:in\s+)?((?:18|19|20)\d{2})\b", re.I), "email": re.compile(r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)}
ABOUT_TERMS = ("about", "press", "company", "our-story", "facts")

class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.title = ""; self.description = ""; self.h1 = ""; self.bits: list[str] = []; self._tag = ""; self.skip = 0
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs); self._tag = tag
        if tag in {"script", "style"}: self.skip += 1
        if tag == "meta" and (data.get("name") or "").lower() == "description": self.description = data.get("content") or ""
    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip: self.skip -= 1
        self._tag = ""
    def handle_data(self, data: str) -> None:
        if self.skip: return
        clean = " ".join(data.split())
        if clean:
            self.bits.append(clean)
            if self._tag == "title": self.title += (" " if self.title else "") + clean
            if self._tag == "h1" and not self.h1: self.h1 = clean

def parse(html: str) -> PageParser:
    parser = PageParser(); parser.feed(html); return parser

def pages_from_dir(root: Path) -> dict[str, str]:
    return {"/" + path.relative_to(root).as_posix(): path.read_text(encoding="utf-8") for path in sorted(root.rglob("*.html")) if path.name != "rendered.html"}

def identity_for(pages: dict[str, str]) -> tuple[str | None, str | None, list[str], str | None]:
    if not pages: return None, None, [], None
    home_url = "/index.html" if "/index.html" in pages else sorted(pages)[0]
    parser = parse(pages[home_url]); title_name = re.split(r"[|–—-]", parser.title, maxsplit=1)[0].strip() or None
    name = title_name or parser.h1 or None
    one_liner = parser.description or next((bit for bit in parser.bits if len(bit.split()) >= 5 and bit not in {parser.title, parser.h1}), None)
    one_liner = unescape(one_liner).strip()[:280] if one_liner else None
    what = [one_liner] if one_liner else []
    return name, one_liner, what, home_url

def extracted_facts(pages: dict[str, str]) -> list[dict[str, object]]:
    observations: dict[str, list[tuple[str, str]]] = {}
    for url, html in sorted(pages.items()):
        visible = anchor_page.text(html)
        for key, pattern in FACT_PATTERNS.items():
            for match in pattern.finditer(visible): observations.setdefault(key, []).append((match.group(1).lower(), url))
    output = []
    for key, pairs in sorted(observations.items()):
        values = sorted({value for value, _ in pairs}); primary = values[0]
        urls = sorted({url for value, url in pairs if value == primary}); contradictions = [{"url": url, "value": value} for value, url in pairs if value != primary]
        output.append({"key": key, "value": primary, "source_urls": urls, "consistent": not contradictions, "contradicted_by": sorted(contradictions, key=lambda item: (item["url"], item["value"])), "quoteable": key == "founded", "check_id": "EF-003"})
    return output

def entity_markup_types(pages: dict[str, str]) -> list[str]:
    """Presence/parse check only; full required-property validation belongs to crawl-render-audit."""
    recognized = {"Organization", "LocalBusiness", "Product", "Service"}; found: set[str] = set()
    for html in pages.values():
        for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
            try: data = json.loads(block)
            except json.JSONDecodeError: continue
            records = data if isinstance(data, list) else [data]
            for record in records:
                if isinstance(record, dict):
                    for kind in record.get("@type", []) if isinstance(record.get("@type"), list) else [record.get("@type")]:
                        if isinstance(kind, str) and kind.rsplit("/", 1)[-1] in recognized: found.add(kind.rsplit("/", 1)[-1])
        for kind in re.findall(r'itemtype=["\'][^"\']*/(Organization|LocalBusiness|Product|Service)["\']', html, re.I): found.add(kind)
    return sorted(found)

def analyse(root: Path) -> dict[str, object]:
    pages = pages_from_dir(root)
    if not pages:
        return {"twin_patch": {"identity": {"name": None, "one_liner": None, "what_they_do": [], "entity_ambiguity_risk": "high", "evidence_refs": []}, "facts": [], "quoteable_facts": 0, "gaps": {"confidently_known": [], "ambiguous": [], "contradicted": []}, "check_execution": {"checked_and_clean": [], "insufficient_evidence": [{"check": "EF-001 through EF-006", "reason": "0 readable HTML pages supplied"}]}}, "findings": []}
    name, one_liner, what, home = identity_for(pages); disambiguation = entity_disambiguation.assess(name, one_liner, pages); anchors = anchor_page.analyse(pages); facts = extracted_facts(pages)
    findings = list(anchors["findings"]); known = [{"fact": f"{fact['key']}: {fact['value']}", "source_url": fact["source_urls"][0], "check_id": "EF-003"} for fact in facts if fact["consistent"]]
    ambiguous: list[str] = []; checked: list[str] = []
    if one_liner: checked.append(f"EF-001 machine-extractable one-line description on {home} (1/{len(pages)} pages)")
    else:
        ambiguous.append("one-line self-description")
        findings.append({"check_id": "EF-001", "title": "No machine-extractable one-line description", "severity": "medium", "chain_link": "understand", "impact_area": "discoverability", "evidence": f"0/{len(pages)} sampled pages supplied a meta description or descriptive home-page sentence; sample: {home}", "suggested_action": "Add one plain-language description to initial HTML and Organization markup."})
    if disambiguation["risk"] in {"high", "medium"}:
        signal_count = sum(bool(v) for key, v in disambiguation["signals"].items() if key != "authoritative_sameAs_present") + int(not disambiguation["signals"]["authoritative_sameAs_present"])
        findings.append({"check_id": "EF-002", "title": "Structural entity ambiguity risk", "severity": "medium" if disambiguation["risk"] == "high" else "low", "chain_link": "verify", "impact_area": "discoverability", "evidence": f"{signal_count}/3 structural ambiguity signals on {home}: common-name={disambiguation['signals']['common_word_or_phrase']}, sameAs={disambiguation['signals']['authoritative_sameAs_present']}, qualifier={disambiguation['signals']['distinguishing_qualifier_present']}", "suggested_action": "State a distinguishing qualifier and link authoritative profiles with sameAs."})
    about = [url for url in pages if any(term in url.lower() for term in ABOUT_TERMS)]
    if about: checked.append(f"EF-004 About/press/facts route detected on {about[0]} (1/{len(pages)} pages)")
    else: ambiguous.append("authoritative about or facts page")
    markup = entity_markup_types(pages)
    if markup:
        checked.append(f"EF-007 identity schema types present: {', '.join(markup)} ({len(markup)}/{len(pages)} sampled pages)")
    else:
        findings.append({"check_id": "EF-007", "title": "No machine-readable entity schema detected", "severity": "medium", "chain_link": "understand", "impact_area": "discoverability", "evidence": f"0/{len(pages)} sampled pages expose Organization, LocalBusiness, Product, or Service markup; sample: {home}", "suggested_action": "Add valid schema.org markup for the site's primary entity type."})
    llms_paths = [path for path in (root / "llms.txt", root / ".well-known" / "llms.txt") if path.is_file()]
    if llms_paths:
        location = "/" + llms_paths[0].relative_to(root).as_posix()
        checked.append(f"EF-006 proactive llms discovery file detected at {location} (1/{len(pages)} HTML pages)")
    contradictory = sorted({fact["key"] for fact in facts if not fact["consistent"]})
    patch = {"identity": {"name": name, "one_liner": one_liner, "what_they_do": what, "entity_ambiguity_risk": disambiguation["risk"], "evidence_refs": []}, "facts": facts, "quoteable_facts": sum(int(fact["quoteable"]) for fact in facts), "gaps": {"confidently_known": known, "ambiguous": sorted(ambiguous), "contradicted": contradictory}, "check_execution": {"checked_and_clean": sorted(checked), "insufficient_evidence": []}}
    return {"twin_patch": patch, "findings": sorted(findings, key=lambda item: (item["check_id"], item["title"]))}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("html_dir", type=Path)
    args = parser.parse_args(argv)
    if not args.html_dir.is_dir(): print("usage error: html_dir must be a directory", file=sys.stderr); return 2
    json.dump(analyse(args.html_dir), sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0
if __name__ == "__main__": raise SystemExit(main())
