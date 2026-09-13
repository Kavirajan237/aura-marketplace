#!/usr/bin/env python3
"""Render a readable, evidence-first AURA audit report."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def render(r):
 c=r['coverage'];t=r['ai_brand_twin'];robots=c['robots'];lines=[f"# AURA audit — {r['site']}","",f"Audited {r['audited_at'][:10]} · {c['pages_sampled']}/{c['pages_estimate']} pages ({c['coverage']:.0%}{', low coverage' if c['low_coverage'] else ''}) · {c['elapsed_ms']/1000:.1f}s · render: {c['render_capability']} · robots: {robots['allowed']}/{robots['checked']} paths allowed",'', '## What an AI currently understands about this brand']
 lines += [f"- {x['fact']} — {x['source_url']}" for x in t['gaps']['confidently_known']] or ['- No fact is sufficiently corroborated in sampled pages.']
 lines += ['',"## What it can't tell / gets wrong"]+[f"- Contradicted: {x}" for x in t['gaps']['contradicted']] or ['- No contradiction established.']
 lines += ['', '## Priority actions','', '| Rank | Finding | Severity | Reach | Owner | First step | How to verify |','|---:|---|---|---:|---|---|---|']
 for i,f in enumerate(r['findings'],1):
  a=f['suggested_action'];lines.append(f"| {i} | {f['title']} | {f['severity']} | {f['affected']['reach_share']:.0%} | {a['owner']} | {a['how'][0]} | {a['validation']} |")
 lines += ['', '## Findings (detail)']
 for f in r['findings']:
  a=f['suggested_action'];p=f['priority_factors'];lines += [f"### {f['id']} — {f['title']}",f"**Evidence:** {f['evidence']}",f"**Mechanism:** {f['mechanism']}",f"**Why it matters:** {f['why_it_matters']}","**How to fix:**",*(f"- {x}" for x in a['how']),f"**Verification:** {a['validation']}",f"**Factors:** impact {p['impact']} · confidence {p['confidence']} · reach {p['reach_share']} · fixability {p['fixability']}",""]
 lines += ['## What we checked and found clean']
 lines += [f'- {x}' for x in r['checked_and_clean']] or ['- No clean checks were recorded.']
 lines += ['', '## What we could not judge, and why']
 lines += [f"- {x['check']}: {x['reason']}" for x in r['insufficient_evidence']] or ['- No abstentions were recorded.']
 lines += ['', '## Limitations', *(f'- {x}' for x in r['limitations'])]
 return '\n'.join(lines)+'\n'
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();text=render(json.loads(a.report.read_text()));a.out.write_text(text,encoding='utf-8') if a.out else print(text)
