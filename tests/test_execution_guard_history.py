"""Historic source-disposition negative tests: no actual rule admission."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_execution_guard_history import REGISTER,FROZEN,LEDGER,validate,pending
class HistoricalIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=json.loads((ROOT/REGISTER).read_text("utf-8"))
        cls.tree=json.loads((ROOT/FROZEN).read_text("utf-8"))
        cls.ledger=json.loads((ROOT/LEDGER).read_text("utf-8"))
    def check(self,r=None):
        return validate(self.reg if r is None else r,self.tree,self.ledger)
    def test_all_3159_sources_pending_not_excluded(self):
        self.assertEqual([],self.check())
        self.assertEqual(3159,self.reg["source_count"])
        self.assertEqual(21,self.reg["source_seed_count"])
        self.assertEqual([],self.reg["reviewed_dispositions"])
        self.assertTrue(pending(self.reg,self.tree))
    def test_machine_rule_pointers_not_owner_admitted(self):
        self.assertEqual(78,sum(len(g["rule_pointers"]) for g in self.reg["candidate_groups"]))
        self.assertTrue(all(not g["owner_admitted"] for g in self.reg["candidate_groups"]))
    def test_fake_complete_state_fails(self):
        bad=copy.deepcopy(self.reg);bad["decisions_complete"]=True
        bad["missing_rules"]=0;bad["unresolved_conflicts"]=0
        self.assertTrue(self.check(bad))
        self.assertTrue(pending(bad,self.tree))
    def test_wrong_candidate_hash_fails(self):
        bad=copy.deepcopy(self.reg);bad["candidate_groups"][0]["source_git_sha"]="0"*40
        self.assertTrue(self.check(bad))
    def test_omitted_candidate_rule_fails(self):
        bad=copy.deepcopy(self.reg);bad["candidate_groups"][0]["rule_pointers"].pop()
        self.assertTrue(self.check(bad))
    def test_unsigned_decision_fails(self):
        bad=copy.deepcopy(self.reg);p,sha,*_=self.tree["files"][0]
        bad["reviewed_dispositions"]=[{"source_path":p,"source_git_sha":sha,
           "decision":"MAPPED_TO_NEW_CANONICAL","owner_evidence_sha256":None}]
        self.assertTrue(self.check(bad))
if __name__=="__main__":unittest.main()
