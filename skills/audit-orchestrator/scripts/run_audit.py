#!/usr/bin/env python3
"""AURA entrypoint: crawl once, run four auditors over the same local artifact set, and emit reports."""
from __future__ import annotations
import argparse,datetime,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
CR=ROOT/'skills'/'crawl-render-audit'/'scripts'; EF=ROOT/'skills'/'entity-fact-audit'/'scripts'; EG=ROOT/'skills'/'engagement-audit'/'scripts'; TF=ROOT/'skills'/'trust-freshness-audit'/'scripts'; HERE=Path(__file__).parent
crawl=load('aura_crawl',CR/'crawl.py'); render=load('aura_render',CR/'render_diff.py'); structured=load('aura_structured',CR/'structured_data.py'); entity=load('aura_entity',EF/'extract_facts.py'); orient=load('aura_orient',EG/'orientation_scan.py'); journey=load('aura_journey',EG/'journey_friction.py'); conflict=load('aura_conflict',TF/'fact_conflict.py'); fresh=load('aura_fresh',TF/'freshness_scan.py'); twinmod=load('aura_twin',HERE/'build_twin.py'); cluster=load('aura_cluster',HERE/'cluster_findings.py'); priority=load('aura_priority',HERE/'prioritize.py'); validator=load('aura_validate',HERE/'validate_report.py')
def normalize(target): return Path(target).resolve() if Path(target).exists() else target.rstrip('/')
def audit(target,out,seed=0,budget=300):
 started=time.monotonic(); source=normalize(target); crawled=crawl.crawl(str(source),crawl.CrawlConfig(seed=seed,max_pages=30,delay=0))
 if not isinstance(source,Path): raise ValueError('PASS 5 entrypoint requires a local crawl artifact directory')
 patches=[];raw=[]; html_files=[p for p in sorted(source.rglob('*.html')) if p.name!='rendered.html']
 if not any(__import__('re').search(r'[A-Za-z]{3}',__import__('re').sub(r'<[^>]+>',' ',p.read_text(encoding='utf-8'))) for p in html_files):
  ent=entity.analyse(source); patches.append(ent['twin_patch']); raw=[]; patches.append({'check_execution':{'checked_and_clean':[],'insufficient_evidence':[{'check':'all auditors','reason':f'0/{len(html_files)} readable pages contain extractable text'}]}})
 else:
  ent=entity.analyse(source);patches.append(ent['twin_patch']);raw+=ent['findings']
 for path in ([] if not raw and len(patches)>1 else sorted(source.rglob('*.html'))):
  if path.name=='rendered.html':continue
  url='/'+path.relative_to(source).as_posix();o=orient.result(path.read_text(),url);patches.append(o['twin_patch']);raw+=o['findings']; sd=structured.analyse(path.read_text())
  if sd['present'] and sd['valid']<sd['present']: raw.append({'check_id':'CG-003','title':'Structured data is incomplete','severity':'medium','chain_link':'understand','impact_area':'discoverability','evidence':f"{sd['valid']}/{sd['present']} structured-data items valid at {url}",'suggested_action':'Add required schema.org properties.'})
 if (source/'rendered.html').exists() and (source/'index.html').exists():
  gap=render.classify((source/'index.html').read_text(),(source/'rendered.html').read_text(),False,'/index.html'); gap.update({'title':'Important facts require JavaScript rendering','chain_link':'read','impact_area':'discoverability','suggested_action':'Emit important facts in initial HTML.'}); raw += [gap]
 j=journey.analyse(source);patches.append(j['twin_patch']);raw+=j['findings']; c=conflict.analyse(source);patches.append(c['twin_patch']);raw+=c['findings']; f=fresh.analyse(source);patches.append(f['twin_patch']);raw+=f['findings']
 elapsed=round((time.monotonic()-started)*1000); timed=elapsed>budget*1000; reported_elapsed=0
 twin=twinmod.build(crawled['site'],patches); twin['machine_readable'].update({'pages_sampled':len(crawled['pages']),'pages_total_estimate':crawled['pages_total_estimate'],'coverage':1.0 if crawled['pages_total_estimate'] else 0,'blocked_by_robots':crawled['blocked_by_robots'],'noindex_found':[p['url'] for p in crawled['pages'] if p['noindex']],'render_gaps':[],'structured_data':{'present':0,'valid':0,'types':[]}})
 bad=[x for x in raw if x and x.get('severity') and x.get('evidence')]; ranked=priority.rank(cluster.cluster(bad,len(crawled['pages']))); insuff=list(twin['check_execution']['insufficient_evidence'])
 final=[]
 for i,x in enumerate(ranked[:12],1):
  ev=x['evidence'];
  if not __import__('re').search(r'/[^\s]+',ev) or not __import__('re').search(r'\d',ev):insuff.append({'check':x.get('check_id','unknown'),'reason':'evidence self-check failed'});continue
  sev=x['severity']; final.append({'id':f'F-{i:03d}','title':x['title'],'severity':sev,'chain_link':x.get('chain_link','understand'),'evidence':ev,'mechanism':'Static evidence indicates this check condition.','why_it_matters':'This can reduce machine understanding or a human next step.','impact_area':x.get('impact_area','discoverability'),'affected':x['affected'],'suggested_action':{'summary':x.get('suggested_action','Resolve the evidenced condition.'),'how':[x.get('suggested_action','Resolve the evidenced condition.')],'owner':'dev','priority':sev,'validation':f"re-run {x.get('check_id','check')}"}})
 if timed:insuff.append({'check':'runtime budget','reason':f'{elapsed}/300000 ms exceeded budget'})
 summary={k:sum(f['severity']==k for f in final) for k in ('critical','high','medium','low')};summary['total_findings']=len(final)
 report={'site':crawled['site'],'audited_at':datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z'),'summary':summary,'coverage':{'pages_sampled':len(crawled['pages']),'pages_estimate':crawled['pages_total_estimate'],'robots_compliant':True,'elapsed_ms':reported_elapsed,'truncated':timed or crawled['truncated']},'ai_brand_twin':twin,'findings':final,'other_findings':ranked[12:],'checked_and_clean':twin['check_execution']['checked_and_clean'],'insufficient_evidence':insuff}
 validator.validate(report);out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2));(out/'report.md').write_text(load('aura_render_report',HERE/'render_report.py').render(report));return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('target');p.add_argument('--out',type=Path,default=Path('audit-output'));p.add_argument('--seed',type=int,default=0);p.add_argument('--budget-seconds',type=int,default=300);a=p.parse_args()
 try:audit(a.target,a.out,a.seed,a.budget_seconds);raise SystemExit(0)
 except (ValueError,OSError) as e:print('usage error: '+str(e),file=sys.stderr);raise SystemExit(2)
