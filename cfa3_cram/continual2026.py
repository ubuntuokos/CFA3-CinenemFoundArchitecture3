"""CFA3-native CPU reference for CRAM 2026 centroid matching (not training).

Reference: LAMDA-CL/EMNLP2026-CRAM @ 576edf0f0a4c23052f275d6a57d36197d4c067ba.
This is an independent non-admitted model-internal expert scoring primitive;
it cannot select an AI provider, allocate experts, train or promote checkpoints.
"""
from dataclasses import dataclass
import math

PIN = "576edf0f0a4c23052f275d6a57d36197d4c067ba"


def _vector(v):
    if not isinstance(v, (tuple, list)) or not v:
        raise ValueError("nonempty centroid vector required")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in v):
        raise ValueError("centroid entries must be finite real numbers")
    n = math.sqrt(sum(x * x for x in v))
    if n <= 0 or not math.isfinite(n):
        raise ValueError("nonzero finite centroid norm required")
    return tuple(x / n for x in v)


@dataclass(frozen=True)
class Expert:
    expert_id: str
    model_revision: str
    projection_id: str
    checkpoint_digest: str
    centroid: tuple[float, ...]

    def __post_init__(self):
        if not self.expert_id or not self.model_revision or not self.projection_id:
            raise ValueError("expert identity and model/projection required")
        if not self.checkpoint_digest.startswith("sha256:") or len(self.checkpoint_digest) != 71:
            raise ValueError("checkpoint digest required")
        if not all(c in "0123456789abcdefABCDEF" for c in self.checkpoint_digest[7:]):
            raise ValueError("invalid checkpoint digest")
        _vector(self.centroid)


@dataclass(frozen=True)
class ExpertMatch:
    expert_id: str | None
    cosine_similarity: float | None
    needs_new_expert_review: bool


def rank_existing_experts(task_centroid, experts, *, model_revision, projection_id, threshold=0.8):
    """Within one preselected model, report best compatible existing expert.

    Does NOT create a new expert, choose a CFA3 Model Router route, authorize
    training or treat a cosine threshold as admission approval.
    """
    v = _vector(task_centroid)
    if not model_revision or not projection_id:
        raise ValueError("model and projection identity required")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise ValueError("finite similarity threshold in [-1,1] required")
    seen = set()
    scored = []
    for expert in experts:
        if not isinstance(expert, Expert) or expert.expert_id in seen:
            raise ValueError("unique typed expert records required")
        seen.add(expert.expert_id)
        if expert.model_revision != model_revision or expert.projection_id != projection_id:
            raise ValueError("expert belongs to another model or projection")
        c = _vector(expert.centroid)
        if len(c) != len(v):
            raise ValueError("centroid dimension mismatch")
        score = sum(a * b for a, b in zip(v, c))
        scored.append((max(-1.0, min(1.0, score)), expert.expert_id))
    if not scored:
        return ExpertMatch(None, None, True)
    score, expert_id = sorted(scored, key=lambda pair: (-pair[0], pair[1]))[0]
    if score < threshold:
        return ExpertMatch(None, score, True)
    return ExpertMatch(expert_id, score, False)
