from __future__ import annotations
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'skills'/'engagement-audit'/'scripts'; T=ROOT/'skills'/'trust-freshness-audit'/'scripts'; F=ROOT/'fixtures'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
orientation=load('orientation',E/'orientation_scan.py'); journey=load('journey',E/'journey_friction.py'); conflict=load('conflict',T/'fact_conflict.py'); freshness=load('freshness',T/'freshness_scan.py')
class Pass4Tests(unittest.TestCase):
 def ids(self,r):return {x['check_id'] for x in r['findings']}
 def test_healthy_no_high_or_critical(self):
  r=orientation.result((F/'pass4-healthy'/'index.html').read_text(),'/index.html');self.assertFalse(any(x['severity'] in {'high','critical'} for x in r['findings']))
 def test_static_friction_proxies_fire(self):
  r=orientation.result((F/'pass4-friction'/'index.html').read_text(),'/index.html');self.assertTrue({'EG-001','EG-008','EG-010','EG-012'}<=self.ids(r))
 def test_navigation_dead_end_and_coverage_are_computable(self):
  r=journey.analyse(F/'pass4-friction');self.assertIn('EG-007',self.ids(r))
 def test_conflict_and_default_corroboration_disclosure(self):
  r=conflict.analyse(F/'pass4-conflicts');self.assertIn('TF-001',self.ids(r));self.assertIn('TF-005 cross-web corroboration',r['twin_patch']['check_execution']['insufficient_evidence'][0]['check'])
 def test_freshness_and_local_hub_failure(self):
  r=freshness.analyse(F/'pass4-conflicts');self.assertTrue({'TF-002','TF-006','TF-007','TF-008'}<=self.ids(r))
 def test_extended_removes_default_disclosure_without_network(self):self.assertFalse(conflict.analyse(F/'pass4-conflicts',True)['twin_patch']['check_execution']['insufficient_evidence'])
if __name__=='__main__':unittest.main()
