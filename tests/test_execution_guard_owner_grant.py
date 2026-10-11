"""Owner-signed approvals, synthetic-only cryptography and no network."""
import copy
import hashlib
import hmac
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from check_execution_rule_evidence import request_digest
from check_execution_guard_owner_grant import (
    SCHEMA, OwnerGrantBlocked, serialized, verify_owner_grant,
)
from check_execution_guard_github_state import (
    live_state_callback, LiveStateBlocked
)
from test_execution_guard_github_state import snapshot

KEY=b"owner-grant-test-only-independent-key".ljust(32,b"_")
NOW=1000.0

def task():
    return {"operation":"REPOSITORY_WRITE", "main_sha":"a"*40,
            "head_sha":"b"*40, "branch":"guard/feature",
            "target":"scripts/execution_guard.py",
            "scope_targets":["scripts/execution_guard.py"],
            "task_id":"synthetic-owner-scope", "nonce":"unique-nonce-12345678",
            "expires_at":NOW+100, "max_units":2, "max_calls":2}

def signed_grant(t):
    grant={"schema":SCHEMA, "approved":True,
           "task_sha256":request_digest(t), "task_id":t["task_id"],
           "nonce":t["nonce"], "operation":t["operation"],
           "target":t["target"], "scope_targets":t["scope_targets"],
           "main_sha":t["main_sha"], "head_sha":t["head_sha"],
           "branch":t["branch"], "issued_at":NOW-1,
           "expires_at":NOW+60}
    grant["signature"]=hmac.new(KEY,serialized(grant),hashlib.sha256).hexdigest()
    return grant

class SignedOwnerGrantTests(unittest.TestCase):
    def test_signed_exact_owner_grant(self):
        t=task()
        self.assertTrue(verify_owner_grant(t,signed_grant(t),KEY,now=NOW))

    def test_no_secret_or_unsigned_callback_accepted(self):
        t=task();g=signed_grant(t)
        for key in (None,b"",b"test", "string"):
            with self.subTest(key=key),self.assertRaises(OwnerGrantBlocked):
                verify_owner_grant(t,g,key,now=NOW)
        g.pop("signature")
        with self.assertRaises(OwnerGrantBlocked):
            verify_owner_grant(t,g,KEY,now=NOW)

    def test_every_task_binding_is_immutable(self):
        t=task();g=signed_grant(t)
        for field,value in (
            ("operation","WORKFLOW_START"),("main_sha","c"*40),
            ("head_sha","c"*40),("branch","guard/else"),
            ("target","docs/new.md"),("scope_targets",["docs/new.md"]),
            ("task_id","other-task"),("nonce","unique-nonce-9876543"),
            ("expires_at",NOW+50),("max_calls",3),("max_units",4)
        ):
            altered=copy.deepcopy(t);altered[field]=value
            with self.subTest(field=field),self.assertRaises(OwnerGrantBlocked):
                verify_owner_grant(altered,g,KEY,now=NOW)

    def test_grant_payload_tampering_and_other_signer_rejected(self):
        t=task();g=signed_grant(t)
        with self.assertRaises(OwnerGrantBlocked):
            verify_owner_grant(t,g,b"wrong-key".ljust(32,b"x"),now=NOW)
        for field,value in (
            ("approved",False),("task_id","made-up"),
            ("expires_at",NOW+10),("schema","fake-schema"),
            ("operation","WORKFLOW_START"),("scope_targets",["scripts/other.py"])
        ):
            changed=copy.deepcopy(g);changed[field]=value
            with self.subTest(field=field),self.assertRaises(OwnerGrantBlocked):
                verify_owner_grant(t,changed,KEY,now=NOW)
        changed=copy.deepcopy(g);changed["extra_permission"]="MERGE"
        with self.assertRaises(OwnerGrantBlocked):
            verify_owner_grant(t,changed,KEY,now=NOW)

    def test_clock_and_expiry_limits(self):
        t=task()
        for field,value in (("issued_at",NOW+1),
                            ("issued_at",NOW-301),
                            ("expires_at",NOW),
                            ("expires_at",NOW+101),
                            ("issued_at",float("nan"))):
            g=signed_grant(t);g[field]=value
            g["signature"]=hmac.new(KEY,serialized({k:v for k,v in g.items() if k!="signature"}),
                                     hashlib.sha256).hexdigest() if value==value else "0"*64
            with self.subTest(field=field,value=value),self.assertRaises(OwnerGrantBlocked):
                verify_owner_grant(t,g,KEY,now=NOW)

    def test_owner_approval_cannot_use_non_github_gate(self):
        t=task();g=signed_grant(t)
        t["operation"]="GUI_RENDER"
        with self.assertRaises(OwnerGrantBlocked):
            verify_owner_grant(t,g,KEY,now=NOW)

    def test_live_adapter_requires_signed_grant_not_bare_true(self):
        with self.assertRaises(LiveStateBlocked):
            live_state_callback("synthetic-token",13,lambda _:True,None)
        with self.assertRaises(LiveStateBlocked):
            live_state_callback("synthetic-token",13,None,KEY)

    def test_live_adapter_signed_owner_grant_positive_with_mock_snapshot(self):
        t=task()
        with patch("check_execution_guard_github_state.TrustedGithubReader.snapshot",
                   return_value=snapshot()), patch(
                       "check_execution_guard_owner_grant.time.time", return_value=NOW):
            callback=live_state_callback("synthetic-token",13,
                                        lambda _:signed_grant(t),KEY)
            proof=callback(t)
            self.assertTrue(proof["owner_scope_approved"])
            self.assertTrue(proof["owner_grant_signature_verified"])

    def test_live_adapter_denies_bare_boolean(self):
        t=task()
        with patch("check_execution_guard_github_state.TrustedGithubReader.snapshot",
                   return_value=snapshot()):
            callback=live_state_callback("synthetic-token",13,lambda _:True,KEY)
            with self.assertRaises(LiveStateBlocked):
                callback(t)

if __name__=="__main__": unittest.main()
