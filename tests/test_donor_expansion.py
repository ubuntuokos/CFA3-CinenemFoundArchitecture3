"""Owner-approved net-new unique filtering and retained URL provenance."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("donor_expansion",ROOT/"scripts/donor_expansion.py")
expansion=importlib.util.module_from_spec(spec)
spec.loader.exec_module(expansion)

def entries(known_count,new_count):
    items=[{"url":"https://github.com/known/x"+str(i),"parent_id":"root","evidence":"known"+str(i)}
           for i in range(known_count)]
    items.extend({"url":"https://github.com/new/y"+str(i),"parent_id":"root","evidence":"new"+str(i)}
                 for i in range(new_count))
    return items

def known(n):
    return {"https://github.com/known/x"+str(i):"KNOWN-"+str(i) for i in range(n)}

def run(items,index):
    return expansion.evaluate(items,index,frozen_l1_b=445,level=2,
                              previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=True)

class NetNewExpansionTests(unittest.TestCase):
    def test_650_links_445_known_205_new(self):
        result=run(entries(445,205),known(445))
        self.assertEqual((result["state"],result["net_new_unique_count"],result["limit"]),
                         ("STAGED_NOT_PUBLISHED",205,511))
        self.assertEqual(len(result["observed_relations"]),650)
        self.assertEqual(result["publication_gate"],"PENDING")

    def test_512_links_all_known_no_reprocessing(self):
        result=run(entries(512,0),known(512))
        self.assertEqual(result["state"],"EARLY_EXHAUSTION_CANDIDATE")
        self.assertEqual(result["net_new_unique_count"],0)
        self.assertEqual(result["known_occurrences"],512)

    def test_800_links_151_known_649_new_triggers_stop(self):
        result=run(entries(151,649),known(151))
        self.assertEqual(result["state"],"STOPPED_EXPANSION_LIMIT")
        self.assertEqual(result["first_exceeding_count"],512)
        self.assertEqual(result["raw_examined_at_stop"],663)
        self.assertEqual(result["new_sources"],[])
        self.assertTrue(result["previously_published_snapshot_preserved"])

    def test_same_new_url_two_parents_preserves_both_edges(self):
        result=run([{"url":"https://github.com/new/repo","parent_id":"a","evidence":"a"},
                    {"url":"https://github.com/new/repo","parent_id":"b","evidence":"b"}],{})
        self.assertEqual(result["net_new_unique_count"],1)
        self.assertEqual(len(result["observed_relations"]),2)

    def test_tracking_alias_does_not_reprocess(self):
        result=run([{"url":"https://github.com/example/repo?utm_source=x","parent_id":"r","evidence":"e"}],
                   {"https://github.com/example/repo":"EXISTING"})
        self.assertEqual(result["net_new_unique_count"],0)
        self.assertEqual(result["observed_relations"][0]["known_source_id"],"EXISTING")

    def test_identity_collision_fail_closed(self):
        result=run([],{"https://github.com/example/repo":"A",
                       "https://github.com/example/repo/":"B"})
        self.assertEqual(result["state"],"UNRESOLVED_IDENTITY_CONFLICT")

    def test_complete_prior_publication_and_index_required(self):
        result=expansion.evaluate(entries(1,1),known(1),frozen_l1_b=445,level=2,
                                  previous_gate="PENDING",index_complete=True)
        self.assertEqual(result["state"],"BLOCKED_PREVIOUS_LEVEL_UNVERIFIED")
        result=expansion.evaluate(entries(1,1),known(1),frozen_l1_b=445,level=2,
                                  previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=False)
        self.assertEqual(result["state"],"BLOCKED_INDEX_INCOMPLETE")

    def test_l4_to_l5_accepted_and_l6_forbidden(self):
        result=expansion.evaluate(entries(0,1),{},frozen_l1_b=445,level=5,
                                  previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=True)
        self.assertEqual(result["state"],"STAGED_NOT_PUBLISHED")
        self.assertEqual(result["new_sources"][0]["global_level"],5)
        self.assertEqual(result["publication_gate"],"PENDING")
        exhausted=expansion.evaluate(entries(1,0),known(1),frozen_l1_b=445,level=5,
                                     previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=True)
        self.assertEqual(exhausted["state"],"EARLY_EXHAUSTION_CANDIDATE")
        with self.assertRaises(ValueError):
            expansion.evaluate(entries(0,1),{},frozen_l1_b=445,level=6,
                               previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=True)

    def test_invalid_frozen_baseline_and_level(self):
        with self.assertRaises(ValueError):
            expansion.evaluate([],{},frozen_l1_b=0,level=2,
                               previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=True)
        with self.assertRaises(ValueError):
            expansion.evaluate([],{},frozen_l1_b=445,level=6,
                               previous_gate="PUBLISHED_AND_VERIFIED_PASS",index_complete=True)

if __name__ == "__main__":
    unittest.main()
