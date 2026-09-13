#!/usr/bin/env python3
"""Optional rendered-HTML capture. Never writes outside the supplied artifact directory."""
from __future__ import annotations
import argparse,os,shlex,subprocess
from pathlib import Path
def capability():
 try: import playwright  # noqa:F401
 except ImportError: return 'browser' if os.environ.get('AURA_BROWSER_CMD') else 'unavailable'
 return 'browser'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('url');p.add_argument('--out',type=Path,required=True);p.add_argument('--timeout-ms',type=int,default=15000);a=p.parse_args()
 if capability()=='unavailable':print('{"rendered":false,"reason":"no browser renderer available"}');return 0
 if not os.environ.get('AURA_BROWSER_CMD'):print('{"rendered":false,"reason":"Playwright detected but capture adapter unavailable"}');return 0
 a.out.parent.mkdir(parents=True,exist_ok=True);completed=subprocess.run(shlex.split(os.environ['AURA_BROWSER_CMD'])+[a.url,str(a.out)],timeout=a.timeout_ms/1000,check=False);print('{"rendered":'+str(completed.returncode==0).lower()+'}');return 0
if __name__=='__main__':raise SystemExit(main())
