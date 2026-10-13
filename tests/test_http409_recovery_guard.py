"""Decision tests for the HTTP 409 v1.1 rule, including fail-closed cases."""
import unittest
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from http409_recovery_guard import authorize_recovery, verify_recovery, execute_recovery, Decision

class Http409GuardTests(unittest.TestCase):
    def setUp(self):
        self.event = dict(http_status=409,method="PUT",endpoint="/repos/x/contents/a",resource="a",operation_id="approved-1",cause="outdated SHA",action="refresh_precondition",attempt=0)
        self.observed = dict(resource="a",version="sha-current",verified_independently=True,fresh=True,precondition_matches=True)
        self.scope = dict(operation_id="approved-1",approved=True,directly_necessary=True)
        self.authority = dict(action_permitted=True,content_decision_required=False)
        self.evidence = dict(third_party_changes_preserved=True,security_gates_pass=True,serialized_write=True,same_failure_repeated=False,failure_recorded=True)
    def decide(self):
        return authorize_recovery(self.event,observed=self.observed,scope=self.scope,authority=self.authority,evidence=self.evidence).decision
    def test_allow_targeted_correction(self):
        self.assertEqual(self.decide(),Decision.ALLOW)
    def test_scope_and_authority_deny(self):
        self.scope["approved"]=False
        self.assertEqual(self.decide(),Decision.STOP)
        self.scope["approved"]=True
        self.authority["action_permitted"]=False
        self.assertEqual(self.decide(),Decision.STOP)
    def test_stale_precondition_recheck(self):
        self.observed["fresh"]=False
        self.assertEqual(self.decide(),Decision.RECHECK)
    def test_untrusted_readback_denied(self):
        self.observed["verified_independently"]=False
        self.assertEqual(self.decide(),Decision.STOP)
    def test_retry_cycle_denied(self):
        self.event["attempt"]=1
        self.assertEqual(self.decide(),Decision.STOP)
    def test_change_loss_denied(self):
        self.evidence["third_party_changes_preserved"]=False
        self.assertEqual(self.decide(),Decision.STOP)
    def test_parallel_write_denied(self):
        self.evidence["serialized_write"]=False
        self.assertEqual(self.decide(),Decision.STOP)
    def test_sensitive_action_denied(self):
        self.event["merge"]=True
        self.assertEqual(self.decide(),Decision.STOP)
    def test_missing_security_and_audit_denied(self):
        self.evidence["security_gates_pass"]=False
        self.assertEqual(self.decide(),Decision.STOP)
        self.evidence["security_gates_pass"]=True
        self.evidence["failure_recorded"]=False
        self.assertEqual(self.decide(),Decision.STOP)
    def test_real_guarded_write(self):
        calls = []
        def inspect(resource):
            return dict(self.observed)
        def write(event, *, expected_version):
            calls.append(expected_version)
            return dict(accepted=True,original_task_resumed=True,unauthorized_changes=False,original_conflict_resolved=True)
        def readback(resource):
            return dict(resource="a",version="sha-new",readback_verified=True)
        result = execute_recovery(self.event,scope=self.scope,authority=self.authority,
                                  evidence=self.evidence,inspect=inspect,write=write,readback=readback)
        self.assertEqual(result.decision,Decision.ALLOW)
        self.assertEqual(calls,["sha-current"])

    def test_no_write_when_state_changed(self):
        calls = []
        revisions = ["sha-current","sha-conflict"]
        def inspect(resource):
            state = dict(self.observed)
            state["version"] = revisions.pop(0)
            return state
        def write(*args,**kwargs):
            calls.append(True)
        result = execute_recovery(self.event,scope=self.scope,authority=self.authority,
                                  evidence=self.evidence,inspect=inspect,write=write,
                                  readback=lambda r: {})
        self.assertEqual(result.decision,Decision.STOP)
        self.assertFalse(calls)

    def test_execution_guard_dispatch_success(self):
        from execution_guard import _http409_guarded_executor
        task = {"task_id":"approved-1","target":"a","operation":"REPOSITORY_WRITE",
                "http_409_recovery":dict(self.event)}
        checked = {"http_409_recovery":{"scope":dict(self.scope),
                   "authority":dict(self.authority),"evidence":dict(self.evidence)}}
        adapters = {"inspect":lambda name:dict(self.observed),
                    "write":lambda event,expected_version:{"accepted":True,
                        "original_task_resumed":True,"unauthorized_changes":False,
                        "original_conflict_resolved":True},
                    "readback":lambda name:{"resource":name,"version":"new",
                        "readback_verified":True}}
        self.assertEqual(_http409_guarded_executor(task,checked,adapters)[0]["decision"],"ALLOW")

    def test_execution_guard_rejects_missing_trusted_proof(self):
        from execution_guard import _http409_guarded_executor, Blocked
        with self.assertRaises(Blocked):
            _http409_guarded_executor({}, {}, {})

    def test_closed_only_on_independent_proof(self):
        b=dict(resource="a",version="old")
        a=dict(resource="a",version="new",readback_verified=True)
        r=dict(original_task_resumed=True,unauthorized_changes=False,original_conflict_resolved=True)
        self.assertEqual(verify_recovery(before=b,after=a,receipt=r).decision,Decision.ALLOW)
        a["readback_verified"]=False
        self.assertEqual(verify_recovery(before=b,after=a,receipt=r).decision,Decision.STOP)

if __name__ == "__main__":
    unittest.main()
