"""CFA3-native, upstream-code-free RAG credibility policy for CrAM 2025.

Reference: Aatrox103/CrAM @ b6403d002a7bb445410f277a73907d7a2e3a8bf1.
Upstream root code license is unverified: no upstream source is imported.
This is a CPU-compatible policy/hook-safety primitive, not runtime admission.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import math
import re

PIN = "b6403d002a7bb445410f277a73907d7a2e3a8bf1"
_DIGEST = re.compile(r"^sha256:[a-fA-F0-9]{64}$")


@dataclass(frozen=True)
class Evidence:
    source_id: str
    digest: str
    credibility: float
    assessor_ref: str

    def __post_init__(self):
        if not self.source_id or not self.assessor_ref or not _DIGEST.fullmatch(self.digest):
            raise ValueError("source, verifiable digest and assessor reference required")
        if isinstance(self.credibility, bool) or not isinstance(self.credibility, (int, float)):
            raise ValueError("credibility must be a number")
        if not math.isfinite(self.credibility) or not 0 <= self.credibility <= 1:
            raise ValueError("credibility must be finite and within [0,1]")


@dataclass(frozen=True)
class SourceTokenSpan:
    source_id: str
    begin: int
    end: int


def attention_log_bias(evidence, spans, token_count, *, floor=0.001):
    """Return per-token *additive* log bias, not a truth score or model action.

    Callers must independently verify assessor signatures and tokenizer-aligned
    spans, then explicitly qualify any model's attention-mask semantics.
    There is NO implicit model loading, CUDA routing or internal credibility AI.
    """
    if not isinstance(token_count, int) or isinstance(token_count, bool) or token_count <= 0:
        raise ValueError("positive token count required")
    if isinstance(floor, bool) or not isinstance(floor, (int, float)) or not math.isfinite(floor) or not 0 < floor <= 1:
        raise ValueError("floor must be finite and in (0,1]")
    by_id = {}
    for item in evidence:
        if not isinstance(item, Evidence) or item.source_id in by_id:
            raise ValueError("unique validated Evidence records required")
        by_id[item.source_id] = item
    if not by_id:
        raise ValueError("empty evidence")
    bias = [0.0] * token_count
    covered = set()
    represented = set()
    for span in spans:
        if not isinstance(span, SourceTokenSpan) or span.source_id not in by_id:
            raise ValueError("unknown or invalid source span")
        if (isinstance(span.begin, bool) or isinstance(span.end, bool)
                or not isinstance(span.begin, int) or not isinstance(span.end, int)
                or not 0 <= span.begin < span.end <= token_count):
            raise ValueError("token span out of bounds")
        if any(t in covered for t in range(span.begin, span.end)):
            raise ValueError("overlapping source token spans")
        represented.add(span.source_id)
        covered.update(range(span.begin, span.end))
        value = math.log(max(floor, by_id[span.source_id].credibility))
        bias[span.begin:span.end] = [value] * (span.end - span.begin)
    if set(by_id) != represented:
        raise ValueError("all assessed source records must have token spans")
    return tuple(bias)


@contextmanager
def temporary_attention_pre_hook(model_module, hook):
    """Brackets an explicitly qualified PyTorch-like hook with guaranteed removal.

    Does not validate actual attention architecture, tensors or permissions.
    Only a separately verified CFA3 adapter may call it during inference.
    """
    handle = model_module.register_forward_pre_hook(hook, with_kwargs=True)
    try:
        yield
    finally:
        handle.remove()
