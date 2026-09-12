from __future__ import annotations
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; S=ROOT/'skills'/'audit-orchestrator'/'scripts';F=ROOT/'fixtures'
def load(n):
 s=importlib.util.spec_from_file_location(n,S/f'{n}.py');m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
run=load('run_audit');cluster=load('cluster_findings');priority=load('prioritize');validate=load('validate_report')
class OrchestratorTests(unittest.TestCase):
 def report(self,name):
  out=ROOT/'work'/('t-'+name);return run.audit(F/name,out,0)
 def test_healthy_no_high_critical(self):self.assertFalse(any(x['severity'] in {'high','critical'} for x in self.report('pass4-healthy')['findings']))
 def test_spa_high_gate(self):self.assertTrue(any(x['title'].startswith('') and x['severity']=='high' for x in self.report('broken-spa')['findings']))
 def test_conflict_merges_twin(self):self.assertTrue(any(not x['consistent'] for x in self.report('conflicting-facts')['ai_brand_twin']['facts']))
 def test_invalid_data_and_empty_evidence(self):
  self.assertTrue(any('Structured data' in x['title'] for x in self.report('shopify-like')['findings']));self.assertFalse(self.report('empty')['findings'])
 def test_robots_and_determinism(self):
  a=self.report('bot-blocked');self.assertTrue(a['ai_brand_twin']['machine_readable']['blocked_by_robots']);x=self.report('pass4-healthy');y=self.report('pass4-healthy');x.pop('audited_at');y.pop('audited_at');self.assertEqual(x,y)
 def test_cluster_reach_top12_and_schema(self):
  c=cluster.cluster([{'check_id':'EG-001','title':'x','evidence':'1/2 at /a','severity':'medium'}]*15,15);self.assertEqual(15,c[0]['affected']['pages']); ranked=priority.rank([dict(c[0],affected={'pages':1,'reach_share':.1,'template':'x'}) for _ in range(13)]);self.assertEqual(13,len(ranked));validate.validate(self.report('pass4-healthy'))
if __name__=='__main__':unittest.main()
