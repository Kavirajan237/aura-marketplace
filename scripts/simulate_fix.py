#!/usr/bin/env python3
"""Apply a safe local counterfactual HTML patch and report whether its originating check flips."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills'/'crawl-render-audit'/'scripts'))
import render_diff
def apply(html,kind):
 if kind=='inject-jsonld': return html.replace('</head>','<script type="application/ld+json">{"@type":"Product","name":"item","offers":{"price":"1"}}</script></head>')
 if kind=='unhide-static': return html.replace('</body>','<p>Price: $1.00. In stock.</p></body>').replace('display:none','display:block').replace(' hidden','')
 if kind=='rewrite-title-h1': return html.replace('<title>','<title>Product for teams — ').replace('<h1>','<h1>Product for teams — ')
 if kind=='dedupe-founded': return html.replace('2020','2021')
 if kind=='insert-value-prop': return html.replace('<body>','<body><p>We provide a clear service for teams.</p>')
 raise ValueError('unknown fix type')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('html',type=Path);p.add_argument('--fix',required=True,choices=['inject-jsonld','unhide-static','rewrite-title-h1','dedupe-founded','insert-value-prop']);p.add_argument('--rendered',type=Path);a=p.parse_args();before=a.html.read_text();after=apply(before,a.fix);out={'fix':a.fix,'before_bytes':len(before),'after_bytes':len(after),'accepted':len(after)>len(before)}
 if a.rendered: out['render_gap_before']=render_diff.classify(before,a.rendered.read_text(),False);out['render_gap_after']=render_diff.classify(after,a.rendered.read_text(),False);out['accepted']=out['render_gap_after']['severity'] is None
 json.dump(out,sys.stdout,sort_keys=True);sys.stdout.write('\n')
