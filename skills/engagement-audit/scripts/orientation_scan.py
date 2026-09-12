#!/usr/bin/env python3
"""Computable engagement proxies from static HTML/CSS; no behavioral claims or network access."""
from __future__ import annotations
import argparse, json, re, sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

CTA_VERBS = ("buy", "start", "get", "contact", "book", "shop", "try", "subscribe", "learn", "sign up")
KEY_FACTS = ("price", "shipping", "return", "hours", "availability", "contact")

class DOM(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.title=""; self.h1=[]; self.headings=[]; self.paragraphs=[]; self.text=[]; self.links=[]; self.buttons=[]; self.styles=[]; self.hidden=[]; self.lang=None; self.hreflang=[]; self._tag=""; self._attrs={}; self._hidden=0
    def handle_starttag(self, tag, attrs):
        d=dict(attrs); self._tag=tag; self._attrs=d
        if tag=="html": self.lang=d.get("lang")
        if tag=="link" and d.get("hreflang"): self.hreflang.append(d.get("hreflang"))
        if tag=="style": self._hidden+=1
        if tag in {"script"}: self._hidden+=1
        if tag in {"a","button"}: (self.links if tag=="a" else self.buttons).append({"text":"", "href":d.get("href",""), "style":d.get("style", ""), "index":len(" ".join(self.text))})
        if "hidden" in d or "display:none" in d.get("style", "").replace(" ", "").lower() or d.get("aria-hidden")=="true": self._hidden+=1
    def handle_endtag(self, tag):
        if tag in {"style","script"} and self._hidden: self._hidden-=1
        self._tag=""
    def handle_data(self, data):
        value=" ".join(data.split())
        if not value: return
        if self._tag=="style": self.styles.append(value); return
        if self._hidden:
            self.hidden.append(value); return
        self.text.append(value)
        if self._tag=="title": self.title += (" " if self.title else "")+value
        if self._tag and re.fullmatch(r"h[1-6]", self._tag): self.headings.append((int(self._tag[1]), value)); self.h1.extend([value] if self._tag=="h1" else [])
        if self._tag=="p": self.paragraphs.append(value)
        if self._tag in {"a","button"}:
            collection=self.links if self._tag=="a" else self.buttons
            if collection: collection[-1]["text"] += (" " if collection[-1]["text"] else "")+value

def words(value: str) -> set[str]: return set(re.findall(r"[a-z]{3,}", value.lower()))
def agreement(a: str, b: str) -> float:
    left,right=words(a),words(b); return 0.0 if not left or not right else len(left&right)/len(left|right)
def ratio(hexcolor: str, background: str) -> float:
    def lum(value):
        rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]; channels=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]; return .2126*channels[0]+.7152*channels[1]+.0722*channels[2]
    a,b=lum(hexcolor),lum(background); return (max(a,b)+.05)/(min(a,b)+.05)
def parse(html: str) -> DOM: dom=DOM(); dom.feed(html); return dom
def ctas(dom: DOM): return [x for x in dom.links+dom.buttons if any(re.search(r"\b"+re.escape(v)+r"\b",x["text"].lower()) for v in CTA_VERBS)]

def analyse_html(html: str, url: str="/index.html") -> dict[str, object]:
    dom=parse(html); text=" ".join(dom.text); calls=sorted(ctas(dom),key=lambda x:(x["index"],x["text"]))
    first=dom.h1[0] if dom.h1 else ""; para=dom.paragraphs[0] if dom.paragraphs else ""; descriptor=" ".join([first,para])
    offering=bool(re.search(r"\b(?:make|offer|service|product|platform|equipment|software|help)\b",descriptor,re.I))
    viewport={"360x640": {"offering":offering and len(descriptor)<=300, "next_step":any(x["index"]<=300 for x in calls)}, "1280x800": {"offering":offering and len(descriptor)<=700, "next_step":any(x["index"]<=700 for x in calls)}}
    levels = [heading[0] for heading in dom.headings]
    hierarchy = len(dom.h1) == 1 and not any(current > previous + 1 for previous, current in zip(levels, levels[1:]))
    semantic=min(agreement(dom.title,first),agreement(first,para)) if dom.title and first and para else 0.0
    styles=" ".join(dom.styles+ [str(x["style"]) for x in calls]); colors=re.findall(r"(?:color|background(?:-color)?)\s*:\s*(#[0-9a-fA-F]{6})",styles); contrast=None
    if len(colors)>=2: contrast=round(ratio(colors[0],colors[1]),2)
    hidden_facts=sorted({fact for fact in KEY_FACTS if any(fact in bit.lower() for bit in dom.hidden)})
    long_blocks=sum(len(p.split())>=250 for p in dom.paragraphs)
    forms=re.findall(r"<form\b.*?</form>",html,re.I|re.S); unlabeled=0
    for form in forms:
        for control in re.findall(r"<(?:input|select|textarea)\b[^>]*>", form, re.I):
            input_id = (re.search(r"\bid=[\"']([^\"']*)[\"']", control, re.I) or [""])[1] if re.search(r"\bid=[\"']([^\"']*)[\"']", control, re.I) else ""
            name = (re.search(r"\bname=[\"']([^\"']*)[\"']", control, re.I) or [""])[1] if re.search(r"\bname=[\"']([^\"']*)[\"']", control, re.I) else ""
            if not input_id and not name: continue
            if not (input_id and re.search(r"<label[^>]+for=[\"']"+re.escape(input_id)+r"[\"']",form,re.I) or re.search(r"(?:aria-label|autocomplete)=",control,re.I)): unlabeled+=1
    targets=[]
    for call in calls:
        dims=re.findall(r"(?:width|height)\s*:\s*(\d+)px",str(call["style"]));
        if len(dims)>=2: targets.append(min(map(int,dims[:2]))>=44)
    first_paint={"bytes":len(html.encode()), "blocking_scripts":len(re.findall(r"<script(?![^>]+(?:defer|async))",html,re.I)), "stylesheets":len(re.findall(r"<link[^>]+rel=[\"']stylesheet",html,re.I))}
    hreflang = sorted(x for x in dom.hreflang if x)
    hreflang_valid = all(re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?|x-default", code or "") for code in hreflang)
    return {"url":url,"viewports":viewport,"heading_hierarchy_ok":hierarchy,"h1_title_first_paragraph_agreement":round(semantic,2),"cta_count":len(calls),"above_fold_cta":viewport["360x640"]["next_step"],"contrast_ratio":contrast,"hidden_key_facts":hidden_facts,"long_unbroken_blocks":long_blocks,"form_unlabeled_controls":unlabeled,"tap_targets_aa": None if not targets else all(targets),"lang":dom.lang,"hreflang":hreflang,"hreflang_valid":hreflang_valid,"page_weight":first_paint}

def result(html: str,url: str="/index.html") -> dict[str,object]:
    scan=analyse_html(html,url); findings=[]; insuff=[]
    def add(cid,title,severity,evidence,chain="orient"):
        findings.append({"check_id":cid,"title":title,"severity":severity,"chain_link":chain,"impact_area":"engagement","evidence":evidence,"suggested_action":"Address the measurable proxy, then rerun this check."})
    v=scan["viewports"]
    if not all(x["offering"] and x["next_step"] for x in v.values()): add("EG-001","First viewport lacks offering or next step","medium",f"{sum(x['offering'] and x['next_step'] for x in v.values())}/2 tested viewports include both at {url}")
    if not scan["heading_hierarchy_ok"]: add("EG-002","Heading hierarchy is not a single ordered outline","low",f"0/1 ordered heading-outline proxy passes at {url}")
    if scan["h1_title_first_paragraph_agreement"]<.2: add("EG-003","Title, H1, and first paragraph lack lexical agreement","low",f"{scan['h1_title_first_paragraph_agreement']:.2f}/1 lexical agreement at {url}")
    if not scan["above_fold_cta"]: add("EG-004","No verb-like CTA in the compact first-view proxy","medium",f"0/{scan['cta_count']} CTAs occur in first 300 text characters at {url}","engage")
    if scan["contrast_ratio"] is not None and scan["contrast_ratio"]<4.5: add("EG-005","Computed CTA color contrast is below WCAG AA","medium",f"{scan['contrast_ratio']:.2f}/4.50 computed contrast ratio at {url}","act")
    if scan["contrast_ratio"] is None: insuff.append({"check":"EG-005 contrast","reason":f"0 computable foreground/background CSS color pairs at {url}"})
    if scan["hidden_key_facts"]: add("EG-008","Key facts are hidden on fresh load","medium",f"{len(scan['hidden_key_facts'])}/{len(KEY_FACTS)} key fact types hidden at {url}: {', '.join(scan['hidden_key_facts'])}")
    if scan["long_unbroken_blocks"]: add("EG-009","Long unbroken text block","low",f"{scan['long_unbroken_blocks']}/1+ paragraphs exceed 250 words at {url}")
    if scan["form_unlabeled_controls"]: add("EG-010","Form controls lack label or autofill proxy","medium",f"{scan['form_unlabeled_controls']}/1+ controls lack label, aria-label, or autocomplete at {url}","act")
    if scan["tap_targets_aa"] is False: add("EG-011","Measured CTA tap target is below 44px","medium",f"0/1 measured CTA targets meet 44px minimum at {url}","act")
    if scan["tap_targets_aa"] is None: insuff.append({"check":"EG-011 tap targets","reason":f"0 CTA targets expose both inline width and height at {url}"})
    if not scan["lang"] or not scan["hreflang_valid"]: add("EG-012","Document language or hreflang metadata is invalid","low",f"{int(bool(scan['lang']))}/{1} html lang and {int(scan['hreflang_valid'])}/{1} hreflang-format checks pass at {url}")
    if scan["page_weight"]["bytes"]>500_000 or scan["page_weight"]["blocking_scripts"]>3: add("EG-013","Static first-paint proxy is heavy","low",f"{scan['page_weight']['bytes']} bytes and {scan['page_weight']['blocking_scripts']} blocking scripts at {url}")
    twin={"human_experience":{"above_fold_states_offering":all(x["offering"] for x in v.values()),"primary_cta_found":scan["above_fold_cta"],"cta_count":scan["cta_count"],"heading_hierarchy_ok":scan["heading_hierarchy_ok"],"h1_title_mismatch":scan["h1_title_first_paragraph_agreement"]<.2},"check_execution":{"checked_and_clean":[],"insufficient_evidence":insuff}}
    return {"twin_patch":twin,"findings":sorted(findings,key=lambda f:f["check_id"]),"metrics":scan}
def main(argv:Iterable[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("html_file",type=Path);p.add_argument("--url",default="/index.html");a=p.parse_args(argv)
    if not a.html_file.is_file(): print("usage error: html_file must exist",file=sys.stderr);return 2
    json.dump(result(a.html_file.read_text(encoding="utf-8"),a.url),sys.stdout,sort_keys=True);sys.stdout.write("\n");return 0
if __name__=="__main__":raise SystemExit(main())
