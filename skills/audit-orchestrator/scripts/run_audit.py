#!/usr/bin/env python3
"""Run one bounded read-only crawl and compose the AURA report."""
from __future__ import annotations
import argparse, datetime, importlib.util, json, re, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
CR=ROOT/'skills'/'crawl-render-audit'/'scripts'; EF=ROOT/'skills'/'entity-fact-audit'/'scripts'; EG=ROOT/'skills'/'engagement-audit'/'scripts'; TF=ROOT/'skills'/'trust-freshness-audit'/'scripts'
sys.path.insert(0,str(CR)) if str(CR) not in sys.path else None
crawl=load('aura_crawl',CR/'crawl.py');render=load('aura_render',CR/'render_diff.py');structured=load('aura_structured',CR/'structured_data.py');entity=load('aura_entity',EF/'extract_facts.py');orient=load('aura_orient',EG/'orientation_scan.py');journey=load('aura_journey',EG/'journey_friction.py');conflict=load('aura_conflict',TF/'fact_conflict.py');fresh=load('aura_fresh',TF/'freshness_scan.py');twinmod=load('aura_twin',HERE/'build_twin.py');cluster=load('aura_cluster',HERE/'cluster_findings.py');priority=load('aura_priority',HERE/'prioritize.py');validator=load('aura_validate',HERE/'validate_report.py')
CAT=json.loads((HERE.parent/'references'/'check-catalogue.json').read_text())
def progress(message): print('[AURA] '+message,file=sys.stderr,flush=True)
def normalize(target): return Path(target).resolve() if Path(target).exists() else target.rstrip('/')
def locator(path,source,crawled):
 rel=path.relative_to(source).as_posix(); artifact=next((p for p in crawled['pages'] if p.get('artifact_path')==rel),None);return artifact['url'] if artifact else '/'+rel
def clean_or_insufficient(checks,insuff):
 return sorted(set(checks)),sorted(insuff,key=lambda x:(x['check'],x['reason']))
def audit(target,out,seed=0,budget=240,max_pages=25,timeout=10.0,delay=.1,work_dir=None):
 begun=time.monotonic(); out=Path(out); requested=normalize(target); local=isinstance(requested,Path)
 if budget<=0: raise ValueError('budget-seconds must be positive')
 cache=Path(work_dir) if work_dir else (ROOT/'work'/((Path(str(requested)).name if local else re.sub(r'[^a-z0-9]+','-',str(requested).split('//')[-1].split('/')[0].lower()).strip('-')+f'-{seed}')))
 artifacts=requested if local else cache/'pages'; progress('validating target and preparing shared crawl')
 crawled=crawl.crawl(str(requested),crawl.CrawlConfig(seed=seed,max_pages=max_pages,timeout=timeout,delay=delay,deadline_seconds=budget),None if local else artifacts)
 if not local: cache.mkdir(parents=True,exist_ok=True);(cache/'crawl.json').write_text(json.dumps(crawled,sort_keys=True,indent=2),encoding='utf-8')
 source=Path(artifacts); html_files=sorted(p for p in source.rglob('*.html') if not p.name.endswith('.rendered.html') and p.name!='rendered.html')
 progress(f"crawl complete: {len(crawled['pages'])} pages; running four read-only auditors")
 patches=[];raw=[];insuff=[];clean=[];render_gaps=[];sd_total={'present':0,'valid':0,'types':[]}
 readable=any(re.search(r'[A-Za-z]{3}',re.sub(r'<[^>]+>',' ',p.read_text(encoding='utf-8',errors='replace'))) for p in html_files)
 ent=entity.analyse(source);patches.append(ent['twin_patch']);raw.extend(ent['findings']) if readable else None
 if not readable: insuff.append({'check':'all auditors','reason':f'0/{len(html_files)} captured pages contain extractable text'})
 for path in html_files:
  html=path.read_text(encoding='utf-8',errors='replace');url=locator(path,source,crawled)
  if readable:
   result=orient.result(html,url);patches.append(result['twin_patch']);raw.extend(result['findings']);insuff.extend(result['twin_patch']['check_execution']['insufficient_evidence'])
   sd=structured.analyse(html);sd_total['present']+=sd['present'];sd_total['valid']+=sd['valid'];sd_total['types']+=sd['types']
   if sd['present'] and sd['valid']<sd['present']: raw.append({'check_id':'CG-003','title':'Structured data is incomplete','severity':'medium','chain_link':'understand','impact_area':'discoverability','evidence':f"{sd['valid']}/{sd['present']} structured-data items valid at {url}",'suggested_action':'Repair required schema.org properties.'})
  rendered=path.with_suffix('.rendered.html')
  if path.name=='index.html' and (source/'rendered.html').exists(): rendered=source/'rendered.html'
  if rendered.exists():
   gap=render.classify(html,rendered.read_text(encoding='utf-8',errors='replace'),False,url);gap['evidence']=gap.get('evidence','')+f'; rendered artifact: /{rendered.relative_to(source).as_posix()}';render_gaps.append({'url':url,'missing_facts':gap['missing_facts'],'confident':bool(gap['severity'])})
   if gap['severity']: gap.update({'title':'Important facts require JavaScript rendering','chain_link':'read','impact_area':'discoverability','suggested_action':'Emit important facts in initial HTML.'});raw.append(gap)
  else:
   missing=[fact for fact in render.IMPORTANT if fact not in render.present_facts(html)]
   suspicious=render.client_rendered(html) and bool(missing);render_gaps.append({'url':url,'missing_facts':missing,'confident':False})
   if suspicious: raw.append({'check_id':'CG-002','title':'Possible JS-render gap — not confirmed','severity':'medium','chain_link':'read','impact_area':'discoverability','evidence':f"{len(missing)}/{len(render.IMPORTANT)} fact types absent at {url}: {', '.join(missing)}; pages_tested: 1/{len(html_files)}; renderer unavailable; gap not confirmed",'suggested_action':'Verify this page in a browser before changing rendering.'})
   else: insuff.append({'check':'CG-002','reason':f'no headless renderer available; render gap untestable at {url}'})
 if readable:
  for result in (journey.analyse(source),conflict.analyse(source),fresh.analyse(source)):
   patches.append(result['twin_patch']);raw.extend(result['findings']);insuff.extend(result['twin_patch']['check_execution']['insufficient_evidence'])
 patches.append({'machine_readable':{'render_gaps':render_gaps,'structured_data':{'present':sd_total['present'],'valid':sd_total['valid'],'types':sorted(sd_total['types'])}}})
 elapsed=round((time.monotonic()-begun)*1000); timed=elapsed>=budget*1000
 if timed or crawled.get('deadline_hit'): insuff.append({'check':'budget','reason':f"stopped after {len(crawled['pages'])} of {crawled['pages_total_estimate']} pages"})
 twin=twinmod.build(crawled['site'],patches);estimated=max(1,crawled['pages_total_estimate']);coverage=min(1.0,len(crawled['pages'])/estimated)
 twin['machine_readable'].update({'pages_sampled':len(crawled['pages']),'pages_total_estimate':crawled['pages_total_estimate'],'coverage':coverage,'blocked_by_robots':crawled['blocked_by_robots'],'noindex_found':[p['url'] for p in crawled['pages'] if p['noindex']]})
 if crawled['blocked_by_robots']: insuff.append({'check':'robots.txt','reason':f"{len(crawled['blocked_by_robots'])} paths refused by robots.txt"})
 ranked=priority.rank(cluster.cluster([x for x in raw if x and x.get('severity') and x.get('evidence')],len(crawled['pages'])))
 final=[]
 for item in ranked:
  if item['severity']=='informational': continue
  if not re.search(r'(?:https?://|/[\w.-]+|#[\w.-]+)',item['evidence']) or not re.search(r'\d',item['evidence']):insuff.append({'check':item['check_id'],'reason':'finding evidence lacks a concrete locator or count'});continue
  spec=CAT[item['check_id']];facts=', '.join(item.get('missing_facts',[])) or 'the measured condition';url=(re.search(r'https?://[^\s,;]+|/[A-Za-z_.-][\w.-]*',item['evidence']) or ["the affected page"])[0]
  how=[step.format(url=url,facts=facts,count=item['affected']['pages']) for step in spec['fix_template']]
  final.append({'id':f"F-{len(final)+1:03d}",'check_id':item['check_id'],'title':item['title'],'severity':item['severity'],'chain_link':spec['chain_link'],'evidence':item['evidence'],'mechanism':spec['mechanism'],'why_it_matters':spec['why_it_matters'],'impact_area':item.get('impact_area','discoverability'),'affected':item['affected'],'priority_points':item['priority_points'],'priority_factors':item['priority_factors'],'suggested_action':{'summary':how[0],'how':how,'owner':spec['owner'],'priority':item['severity'],'validation':f"Re-run {item['check_id']} for {url}"}})
  if len(final)==12: break
 clean,insuff=clean_or_insufficient(twin['check_execution']['checked_and_clean'],insuff+twin['check_execution']['insufficient_evidence'])
 summary={level:sum(f['severity']==level for f in final) for level in ('critical','high','medium','low')};summary['total_findings']=len(final)
 robots={'checked':len(crawled['pages'])+len(crawled['blocked_by_robots']),'allowed':len(crawled['pages']),'refused':crawled['blocked_by_robots']}
 report={'report_version':'2.0','site':crawled['site'],'audited_at':datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z'),'summary':summary,'coverage':{'pages_sampled':len(crawled['pages']),'pages_estimate':crawled['pages_total_estimate'],'coverage':coverage,'low_coverage':coverage<.05,'robots':robots,'elapsed_ms':elapsed,'truncated':timed or crawled['truncated'],'render_capability':'browser' if any(p.with_suffix('.rendered.html').exists() for p in html_files) else 'heuristic'},'ai_brand_twin':twin,'findings':final,'other_findings':[x for x in ranked if x['severity']=='informational' or x not in ranked[:len(final)]],'checked_and_clean':clean,'insufficient_evidence':insuff,'limitations':['Public read-only crawl only.','External corroboration is disabled unless explicitly enabled.','Render results are unconfirmed when no rendered artifact is captured.']}
 progress('validating evidence and rendering report');validator.validate(report);out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2),encoding='utf-8');(out/'report.md').write_text(load('aura_markdown',HERE/'render_report.py').render(report),encoding='utf-8');progress('complete: report.json and report.md written');return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('target');p.add_argument('--out',type=Path,default=Path('audit-output'));p.add_argument('--work-dir',type=Path);p.add_argument('--seed',type=int,default=0);p.add_argument('--budget-seconds',type=int,default=240);p.add_argument('--max-pages',type=int,default=25);p.add_argument('--timeout',type=float,default=10.0);p.add_argument('--delay',type=float,default=.1);a=p.parse_args()
 try:audit(a.target,a.out,a.seed,a.budget_seconds,a.max_pages,a.timeout,a.delay,a.work_dir)
 except (ValueError,OSError,KeyError) as exc: print('usage error: '+str(exc),file=sys.stderr);raise SystemExit(2)
