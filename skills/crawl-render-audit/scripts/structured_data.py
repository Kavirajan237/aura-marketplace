#!/usr/bin/env python3
"""Extract and validate JSON-LD, Microdata, and RDFa without third-party dependencies."""
from __future__ import annotations
import argparse, json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

REQUIRED = {"Organization": ("name",), "LocalBusiness": ("name", "address"), "Product": ("name", "offers"), "Service": ("name", "description"), "WebSite": ("name", "url")}

class Markup(HTMLParser):
    def __init__(self) -> None: super().__init__(); self.json_ld: list[str] = []; self._script = False; self._bits: list[str] = []; self.micro: list[dict[str, object]] = []; self.rdfa: list[dict[str, object]] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs); self._script = tag == "script" and (d.get("type") or "").lower() == "application/ld+json"
        if "itemscope" in d:
            item: dict[str, object] = {"@type": (d.get("itemtype") or "").rstrip("/").split("/")[-1]}; self.micro.append(item)
        if d.get("itemprop") and self.micro: self.micro[-1][d["itemprop"]] = d.get("content") or d.get("href") or d.get("src") or "present"
        if d.get("typeof"):
            item = {"@type": (d.get("typeof") or "").split(":")[-1]}; self.rdfa.append(item)
        if d.get("property") and self.rdfa: self.rdfa[-1][d["property"].split(":")[-1]] = d.get("content") or d.get("href") or "present"
    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script: self.json_ld.append("".join(self._bits)); self._bits = []; self._script = False
    def handle_data(self, data: str) -> None:
        if self._script: self._bits.append(data)

def normalise(value: object) -> list[dict[str, object]]:
    if isinstance(value, list): return [x for item in value for x in normalise(item)]
    if isinstance(value, dict) and "@graph" in value: return normalise(value["@graph"])
    return [value] if isinstance(value, dict) else []

def analyse(html: str) -> dict[str, object]:
    parser = Markup(); parser.feed(html); items: list[dict[str, object]] = []; invalid_json = 0
    for block in parser.json_ld:
        try: items.extend(normalise(json.loads(block)))
        except json.JSONDecodeError: invalid_json += 1
    items.extend(parser.micro); items.extend(parser.rdfa)
    inspected = []
    for item in items:
        raw_type = item.get("@type", ""); types = raw_type if isinstance(raw_type, list) else [raw_type]
        schema_type = next((str(t).rstrip("/").split("/")[-1] for t in types if str(t).rstrip("/").split("/")[-1] in REQUIRED), None)
        if schema_type:
            missing = [prop for prop in REQUIRED[schema_type] if not item.get(prop)]
            inspected.append({"type": schema_type, "valid": not missing, "missing_required": missing})
    return {"present": len(items), "valid": sum(x["valid"] for x in inspected), "types": sorted(x["type"] for x in inspected), "invalid_json_ld": invalid_json, "items": inspected}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("html_file", type=Path); args = parser.parse_args(argv)
    json.dump(analyse(args.html_file.read_text(encoding="utf-8")), sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0
if __name__ == "__main__": raise SystemExit(main())
