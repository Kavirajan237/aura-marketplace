#!/usr/bin/env python3
"""Render a non-expert Markdown audit report."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def render(r):
 lines=[f"# AURA audit: {r['site']}","",f"Sampled {r['coverage']['pages_sampled']} pages; {r['summary']['total_findings']} evidence-backed findings.",""]
 for f in r['findings']: lines += [f"## {f['id']} — {f['title']}",f"**Symptom:** {f['evidence']}",f"**Cost:** {f['why_it_matters']}",f"**Owner/action:** {f['suggested_action']['owner']} — {f['suggested_action']['summary']}",""]
 return '\n'.join(lines)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();text=render(json.loads(a.report.read_text()));a.out.write_text(text) if a.out else print(text)
