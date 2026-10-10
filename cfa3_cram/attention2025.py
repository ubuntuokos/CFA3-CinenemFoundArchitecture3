"""CPU-only, independent CFA3 CrAM 2025 attention qualification adapter.

This module uses PyTorch's public scaled_dot_product_attention operation,
not hooks or unlicensed upstream CrAM code. It is a model-level CPU test
fixture only: rights, assessor identity, Model Router, HRB, Workload Mode and
Security admission have to be checked by external CFA3 authorities.
"""

from __future__ import annotations

import math

try:
    import torch
    import torch.nn.functional as F
except ImportError:
    torch = None
    F = None


class AttentionBackendUnavailable(RuntimeError):
    """PyTorch CPU or an explicitly supported attention configuration is absent."""


def credibility_sdpa_cpu(query, key, value, additive_log_bias, *, causal=False):
    """Return attention with an explicitly supplied credibility log-bias.

    Expected tensor layout: (batch, heads, tokens, head_dim). The caller
    supplies one finite, non-positive additive log-bias per key token, after
    independently validating source/assessment provenance and token mapping.
    Causal masking is allowed only for equal-length self-attention. This
    operation does not select a model or verify decision references.
    """
    if torch is None or F is None:
        raise AttentionBackendUnavailable("optional PyTorch CPU backend absent")
    if not all(isinstance(t, torch.Tensor) for t in (query, key, value)):
        raise ValueError("query, key and value must be PyTorch tensors")
    if any(t.device.type != "cpu" for t in (query, key, value)):
        raise AttentionBackendUnavailable("explicit CPU path only, no backend fallback")
    if any(t.ndim != 4 for t in (query, key, value)):
        raise ValueError("expected B,H,T,D tensor layout")
    if any(t.dtype not in (torch.float32, torch.float64) for t in (query, key, value)):
        raise ValueError("only floating CPU float32/float64 tensors are qualified")
    if query.dtype != key.dtype or query.dtype != value.dtype:
        raise ValueError("query, key and value must have the same dtype")
    b, h, q, d = query.shape
    bk, hk, k, dk = key.shape
    bv, hv, kv, _ = value.shape
    if min(b, h, q, d, k, dk, kv) < 1:
        raise ValueError("empty attention dimension")
    if (bk, hk) != (b, h) or (bv, hv) != (b, h) or d != dk or k != kv:
        raise ValueError("incompatible query/key/value shapes")
    if causal not in (True, False) or not isinstance(causal, bool):
        raise ValueError("causal must be a boolean")
    if causal and q != k:
        raise ValueError("only equal-length causal self-attention is supported")
    if not isinstance(additive_log_bias, (list, tuple)) or len(additive_log_bias) != k:
        raise ValueError("one log-bias per key token is required")
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not math.isfinite(x) or x > 0 for x in additive_log_bias):
        raise ValueError("log-bias entries must be finite and non-positive")
    if any(not bool(torch.isfinite(t).all()) for t in (query, key, value)):
        raise ValueError("non-finite attention tensor")
    with torch.no_grad():
        bias = torch.tensor(additive_log_bias, dtype=query.dtype).reshape(1, 1, 1, k)
        if causal:
            # Exact mask, no implicit Q/K alignment guesswork.
            indices = torch.arange(k)
            upper = indices.unsqueeze(0) > indices.unsqueeze(1)
            bias = bias.expand(1, 1, q, k).clone().masked_fill(upper, float("-inf"))
    return F.scaled_dot_product_attention(query, key, value,
                                           attn_mask=bias, dropout_p=0.0, is_causal=False)
