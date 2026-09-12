#!/usr/bin/env python3
"""Static freshness and internal-link-hub checks; no external corroboration or network access."""
from __future__ import annotations
import argparse,json,re,sys
from datetime import date
from pathlib import Path
from typing import Iterable
def pages(root:Path)->dict[str,str]:return {"/"+p.relative_to(root).as_posix():p.read_text(encoding="utf-8") for p in sorted(root.rglob("*.html"))}
def analyse(root:Path)->dict[str,object]:
 source=pages(root);findings=[];years=[];copyright=[];bad=[];dead_contact=[]
 for url,html in source.items():
  years += [(url,int(y)) for y in re.findall(r"\b(20\d{2})\b",html)]
  copyright += [(url,int(y)) for y in re.findall(r"(?:©|copyright)\s*(20\d{2})",html,re.I)]
  for href in re.findall(r'<a[^>]+href=["\']([^"\'#?]+)',html,re.I):
   target="/"+str((Path(url).parent/href)).replace("\\","/").lstrip("/")
   if target not in source and not href.startswith(("mailto:","tel:","http")):bad.append((url,href))
  for href,label in re.findall(r'<a[^>]+href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',html,re.I|re.S):
   if "contact" in re.sub(r"<[^>]+>","",label).lower() and (not href or href == "#" or (not href.startswith(("mailto:","tel:","http")) and "/"+str((Path(url).parent/href)).replace("\\","/").lstrip("/") not in source)): dead_contact.append((url,href or "#"))
 if years and copyright and max(y for _,y in years)>max(y for _,y in copyright):findings.append({"check_id":"TF-002","title":"Copyright year trails newest dated content","severity":"low","chain_link":"trust","impact_area":"discoverability","evidence":f"{max(y for _,y in copyright)}/{max(y for _,y in years)} copyright/newest-content year; sample: {copyright[0][0]}","suggested_action":"Update footer year or clarify archival content dates."})
 stale_price=[]
 for url,html in source.items():
  if re.search(r"[$€£]\s*\d",html) and not re.search(r"(?:updated|effective|valid)\b",html,re.I):stale_price.append(url)
 if stale_price:findings.append({"check_id":"TF-006","title":"Pricing lacks date context","severity":"low","chain_link":"trust","impact_area":"discoverability","evidence":f"{len(stale_price)}/{len(source)} sampled pages show price without date context; sample: {stale_price[0]}","suggested_action":"Add effective/updated date where price volatility matters."})
 if bad:findings.append({"check_id":"TF-007","title":"Internal link target fails in sampled artifact","severity":"medium","chain_link":"verify","impact_area":"discoverability","evidence":f"{len(bad)}/{len(source)} sampled pages link to missing local target; sample: {bad[0][0]}→{bad[0][1]}","suggested_action":"Repair the hub link or supply the target page."})
 if dead_contact:findings.append({"check_id":"TF-008","title":"Contact route points to an unavailable sampled channel","severity":"medium","chain_link":"trust","impact_area":"discoverability","evidence":f"{len(dead_contact)}/{len(source)} sampled pages contain a contact link with unavailable target; sample: {dead_contact[0][0]}→{dead_contact[0][1]}","suggested_action":"Repair the contact destination and retain a visible contact method."})
 return {"twin_patch":{"check_execution":{"checked_and_clean":[],"insufficient_evidence":[]}},"findings":sorted(findings,key=lambda x:x["check_id"]),"metrics":{"dated_pages":len(set(u for u,_ in years)),"latest_dated_year":max((y for _,y in years),default=None),"broken_hub_links":len(bad),"dead_contact_channels":len(dead_contact)}}
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("html_dir",type=Path);a=p.parse_args(argv)
 if not a.html_dir.is_dir():print("usage error: html_dir must be directory",file=sys.stderr);return 2
 json.dump(analyse(a.html_dir),sys.stdout,sort_keys=True);sys.stdout.write("\n");return 0
if __name__=="__main__":raise SystemExit(main())
