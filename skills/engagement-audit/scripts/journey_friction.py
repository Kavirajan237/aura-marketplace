#!/usr/bin/env python3
"""Navigation and onward-path proxies from a local sampled HTML directory."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

INTENT_WORDS=("price","buy","support","contact","help","product","service")
def pages(root:Path)->dict[str,str]: return {"/"+p.relative_to(root).as_posix():p.read_text(encoding="utf-8") for p in sorted(root.rglob("*.html"))}
def links(html:str)->list[str]: return sorted(set(re.findall(r'<a[^>]+href=["\']([^"\'#?]+)',html,re.I)))
def nav_links(html:str)->list[str]:
    nav=" ".join(re.findall(r"<nav\b.*?</nav>",html,re.I|re.S));return links(nav)
def normal(url:str,href:str)->str:
    if href.startswith("/"): return href
    return "/"+str(Path(url).parent.joinpath(href)).replace("\\","/").lstrip("/")
def sitemap(root:Path)->set[str]:
    p=root/"sitemap.xml"
    if not p.exists():return set()
    try:return {"/"+Path((x.text or "").split("/")[-1]).as_posix() for x in ET.parse(p).iter() if x.tag.endswith("loc")}
    except ET.ParseError:return set()
def analyse(root:Path)->dict[str,object]:
    source=pages(root); site=set(source); nav=set()
    outgoing={}
    for url,html in source.items():
        resolved={normal(url,x) for x in links(html)}; outgoing[url]=resolved&site; nav|={normal(url,x) for x in nav_links(html)}
    map_urls=sitemap(root); candidates=(map_urls or site)-{"/index.html"}; uncovered=sorted(candidates-nav)
    dead=[url for url,html in source.items() if any(w in re.sub(r"<[^>]+>"," ",html).lower() for w in INTENT_WORDS) and not outgoing[url]]
    findings=[]
    if uncovered: findings.append({"check_id":"EG-006","title":"Sitemap pages are absent from navigation","severity":"low","chain_link":"engage","impact_area":"engagement","evidence":f"{len(uncovered)}/{len(candidates)} sitemap-or-sampled pages are not linked from nav; sample: {uncovered[0]}","suggested_action":"Expose primary intent pages through semantic navigation."})
    if dead: findings.append({"check_id":"EG-007","title":"Intent page has no onward internal path","severity":"medium","chain_link":"act","impact_area":"engagement","evidence":f"{len(dead)}/{len(source)} intent-bearing pages have zero onward sampled links; sample: {dead[0]}","suggested_action":"Add a relevant next step or canonical intent path."})
    return {"twin_patch":{"check_execution":{"checked_and_clean":[],"insufficient_evidence":[]}},"findings":findings,"metrics":{"pages":len(source),"nav_coverage":0 if not candidates else round((len(candidates)-len(uncovered))/len(candidates),3),"dead_ends":dead}}
def main(argv:Iterable[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("html_dir",type=Path);a=p.parse_args(argv)
    if not a.html_dir.is_dir():print("usage error: html_dir must be directory",file=sys.stderr);return 2
    json.dump(analyse(a.html_dir),sys.stdout,sort_keys=True);sys.stdout.write("\n");return 0
if __name__=="__main__":raise SystemExit(main())
