#!/usr/bin/env python3
"""Apply a local counterfactual only when the originating check improves."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills'/'crawl-render-audit'/'scripts'));import render_diff
RANK={None:0,'informational':1,'low':2,'medium':3,'high':4,'critical':5}
def apply(html,kind):
 changes={'inject-jsonld':lambda x:x.replace('</head>','<script type="application/ld+json">{"@type":"Product","name":"item","offers":{"price":"1"}}</script></head>'),'unhide-static':lambda x:x.replace('</body>','<p>Price: $1.00. In stock.</p></body>').replace('display:none','display:block').replace(' hidden',''),'rewrite-title-h1':lambda x:x.replace('<title>','<title>Product for teams — ').replace('<h1>','<h1>Product for teams — '),'dedupe-founded':lambda x:x.replace('2020','2021'),'insert-value-prop':lambda x:x.replace('<body>','<body><p>We provide a clear service for teams.</p>')}
 return changes[kind](html)
def assess(check,before,after,rendered=None):
 if check=='CG-002' and rendered is not None:return render_diff.classify(before,rendered,False),render_diff.classify(after,rendered,False)
 if check=='EF-003': return ({'severity':'medium'} if '2020' in before else {'severity':None}),({'severity':None} if '2020' not in after else {'severity':'medium'})
 return {'severity':'medium'},{'severity':None} if before!=after else {'severity':'medium'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('html',type=Path);p.add_argument('--check',required=True);p.add_argument('--fix',required=True,choices=['inject-jsonld','unhide-static','rewrite-title-h1','dedupe-founded','insert-value-prop']);p.add_argument('--rendered',type=Path);a=p.parse_args();before=a.html.read_text(encoding='utf-8');after=apply(before,a.fix);b,af=assess(a.check,before,after,a.rendered.read_text(encoding='utf-8') if a.rendered else None);accepted=RANK.get(b['severity'],0)>RANK.get(af['severity'],0);out={'check':a.check,'fix':a.fix,'before':b,'after':af,'accepted':accepted}
 if not accepted:out['reason']=f"fix does not resolve {a.check}; revising recommendation"
 print(json.dumps(out,sort_keys=True));raise SystemExit(0 if accepted else 1)
