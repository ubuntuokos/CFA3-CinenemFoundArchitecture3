"""Exact CFA3 capability/coverage authority boundaries for the new Current Host.

Target 200 *distinct*, source-reconciled capability IDs. The prior legacy 175
proof matrix is immutable historical material, not transferrable admission.
No generated fixture or externally supplied string can mint physical PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


CAPABILITY_TARGET = 200
CASES = ("POSITIVE", "NEGATIVE", "ROLLBACK")
_ALLOWED_OWNERS = frozenset(("CFA3_COMPONENT", "CFA3_CONNECTOR", "CFA3_PLUGIN_HOST"))
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Capability:
    capability_id: str
    component_id: str
    layer: str
    revision: str
    owner: str
    source_ref: str

    def __post_init__(self):
        if any(not isinstance(v, str) or not v.strip()
               for v in (self.capability_id, self.component_id, self.layer,
                         self.revision, self.source_ref)):
            raise CatalogError("capability identity, version and provenance required")
        if self.owner not in _ALLOWED_OWNERS:
            raise CatalogError("external vendor/plugin capabilities cannot be CFA3 proof targets")


@dataclass(frozen=True)
class ScopedEvidence:
    capability_id: str
    case: str
    component_revision: str
    hardware_scope_digest: str
    evidence_digest: str
    authority_receipt: str
    observed_physical: bool
    observed_result: str

    def __post_init__(self):
        if (self.case not in CASES or not self.capability_id
                or not self.component_revision or not self.authority_receipt
                or not _SHA.fullmatch(self.hardware_scope_digest)
                or not _SHA.fullmatch(self.evidence_digest)):
            raise CatalogError("invalid positive/negative/rollback evidence scope")


class CapabilityCatalog:
    def __init__(self):
        self._items: dict[str, Capability] = {}

    def register(self, item: Capability):
        if not isinstance(item, Capability):
            raise CatalogError("typed CFA3 capability record required")
        if item.capability_id in self._items:
            raise CatalogError("capability identity collision")
        self._items[item.capability_id] = item

    @property
    def registered(self) -> int:
        return len(self._items)

    def reconciliation(self) -> dict:
        count = len(self._items)
        missing = max(0, CAPABILITY_TARGET - count)
        if count != CAPABILITY_TARGET:
            return {
                "status": "BLOCKED_INCOMPLETE_200_CAPABILITY_CATALOG",
                "registered": count, "required": CAPABILITY_TARGET,
                "missing": missing, "overflow": max(0, count - CAPABILITY_TARGET),
                "physical_current_host_pass": False,
            }
        return {
            "status": "STRUCTURAL_200_READY_PENDING_CANONICAL_REVIEW",
            "registered": count, "required": CAPABILITY_TARGET,
            "obligation_count": count * len(CASES),
            "physical_current_host_pass": False,
        }

    def required_cases(self):
        """Return exactly three minimal proof obligations per registered unit."""
        return tuple((cap, case) for cap in sorted(self._items) for case in CASES)

    def review_evidence(self, records: tuple[ScopedEvidence, ...]) -> dict:
        baseline = self.reconciliation()
        if self.registered != CAPABILITY_TARGET:
            return baseline
        required = set(self.required_cases())
        supplied = {}
        for r in records:
            if not isinstance(r, ScopedEvidence):
                raise CatalogError("typed physical evidence record required")
            key = (r.capability_id, r.case)
            if key not in required or key in supplied:
                return {"status": "BLOCKED_UNKNOWN_OR_DUPLICATE_PROOF",
                        "physical_current_host_pass": False}
            cap = self._items[r.capability_id]
            if (r.component_revision != cap.revision or not r.observed_physical
                    or r.observed_result != "PASS"):
                return {"status": "BLOCKED_INCORRECT_SCOPE_OR_NONPHYSICAL_PROOF",
                        "physical_current_host_pass": False}
            supplied[key] = r
        if set(supplied) != required:
            return {"status": "PENDING_MISSING_PROOF_CASES",
                    "received": len(supplied), "required": len(required),
                    "physical_current_host_pass": False}
        # Only a separately admitted Evidence authority may authenticate actual
        # physical hardware identity, signer, receipt and whole-system scope.
        return {"status": "PENDING_EXTERNAL_PHYSICAL_EVIDENCE_AUTHORITY",
                "received": len(supplied), "required": len(required),
                "physical_current_host_pass": False}


def load_capability_catalog(filename):
    """Load canonical-format data WITHOUT inventing unregistered capability IDs."""
    import json
    from pathlib import Path
    try:
        payload = json.loads(Path(filename).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise CatalogError("capability catalog cannot be read as UTF-8 JSON") from exc
    if (not isinstance(payload, dict)
            or set(payload) != {"schema", "capabilities"}
            or payload["schema"] != "cfa3.current-host.capabilities.v1"
            or not isinstance(payload["capabilities"], list)):
        raise CatalogError("capability manifest schema mismatch")
    out = CapabilityCatalog()
    required = {"capability_id", "component_id", "layer", "revision",
                "owner", "source_ref"}
    for record in payload["capabilities"]:
        if not isinstance(record, dict) or set(record) != required:
            raise CatalogError("incomplete capability record")
        out.register(Capability(**record))
    return out
