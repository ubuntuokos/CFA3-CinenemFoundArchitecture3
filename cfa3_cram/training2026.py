"""Isolated CPU qualification prototype for a CRAM 2026 low-rank expert.

This is not the upstream CRAM training algorithm, a Model Router, a runtime
admission decision, or a complete multimodal continual instruction tuner.
It exercises an explicitly scoped adaptive-rank, isolated expert with a
bounded, reversible optimization step on small synthetic CPU tensors.
"""

from __future__ import annotations

import math

try:
    import torch
except ImportError:
    torch = None


SOURCE_REVISION = '576edf0f0a4c23052f275d6a57d36197d4c067ba'


class TrainingBackendUnavailable(RuntimeError):
    """The optional CPU PyTorch training fixture is unavailable."""


def propose_adaptive_rank(gap, *, min_rank=1, max_rank=8):
    """Propose a rank without allocating a real expert or asserting approval."""
    if isinstance(gap, bool) or not isinstance(gap, (int, float)) or not math.isfinite(gap) or not 0 <= gap <= 1:
        raise ValueError('finite gap in [0,1] required')
    if any(isinstance(r, bool) or not isinstance(r, int) or r < 1 for r in (min_rank, max_rank)) or min_rank > max_rank:
        raise ValueError('valid bounded rank interval required')
    return min_rank + math.ceil(gap * (max_rank - min_rank))


class IsolatedLowRankExpert2026CPU:
    """Toy residual adapter: external model and other experts stay unchanged.

    Input features must already originate from one externally selected model.
    This object does not decide whether a new expert is allowed: a real CFA3
    authority must admit and invoke the adapter after relevant approvals.
    """

    def __init__(self, *, input_dim, output_dim, model_revision, projection_id,
                 expert_id, rank_gap, max_rank=8, min_rank=1, seed=0):
        if torch is None:
            raise TrainingBackendUnavailable('CPU PyTorch backend missing')
        for name, val in [('input_dim', input_dim), ('output_dim', output_dim)]:
            if isinstance(val, bool) or not isinstance(val, int) or val < 1:
                raise ValueError(f'{name} must be a positive integer')
        if not all(isinstance(v, str) and v.strip() for v in (model_revision, projection_id, expert_id)):
            raise ValueError('model/projection/expert identity is required')
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError('nonnegative deterministic seed required')
        self.input_dim, self.output_dim = input_dim, output_dim
        self.model_revision, self.projection_id, self.expert_id = model_revision, projection_id, expert_id
        self.rank = propose_adaptive_rank(rank_gap, min_rank=min_rank, max_rank=max_rank)
        if self.rank > min(input_dim, output_dim):
            raise ValueError('rank cannot exceed minimum feature dimension')
        gen = torch.Generator(device='cpu').manual_seed(seed)
        self.a = torch.nn.Parameter(torch.randn(input_dim, self.rank, generator=gen) * 0.025)
        self.b = torch.nn.Parameter(torch.zeros(self.rank, output_dim, dtype=torch.float32))
        self.last_loss = None

    def forward(self, features):
        self._validate_features(features)
        return features @ self.a @ self.b

    def _validate_features(self, features):
        if (not isinstance(features, torch.Tensor) or features.device.type != 'cpu'
                or features.dtype != torch.float32 or features.ndim != 2
                or features.shape[0] < 1 or features.shape[1] != self.input_dim
                or not bool(torch.isfinite(features).all())):
            raise ValueError('finite CPU float32 [N,input_dim] features required')

    def checkpoint(self):
        return {
            'source_revision': SOURCE_REVISION,
            'model_revision': self.model_revision,
            'projection_id': self.projection_id,
            'expert_id': self.expert_id,
            'rank': self.rank,
            'a': self.a.detach().clone(),
            'b': self.b.detach().clone(),
            'last_loss': self.last_loss,
        }

    def restore(self, state):
        for k, expected in [
            ('source_revision', SOURCE_REVISION), ('model_revision', self.model_revision),
            ('projection_id', self.projection_id), ('expert_id', self.expert_id),
            ('rank', self.rank),
        ]:
            if state.get(k) != expected:
                raise ValueError(f'incompatible expert checkpoint: {k}')
        for name, ref in (('a', self.a), ('b', self.b)):
            v = state.get(name)
            if (not isinstance(v, torch.Tensor) or v.device.type != 'cpu'
                    or v.dtype != torch.float32 or v.shape != ref.shape
                    or not bool(torch.isfinite(v).all())):
                raise ValueError(f'invalid checkpoint tensor: {name}')
        loss = state.get('last_loss')
        if loss is not None and (not isinstance(loss, float) or not math.isfinite(loss)):
            raise ValueError('invalid checkpoint loss')
        with torch.no_grad():
            self.a.copy_(state['a'])
            self.b.copy_(state['b'])
        self.last_loss = loss

    def fit(self, features, residual_targets, *, steps=20, lr=0.1,
            orthogonality_refs=(), orthogonality_weight=0.0):
        """Fit one isolated expert, rolling its parameters back on any failure.

        Previous experts are frozen reference matrices only. Failure rollback
        covers this adapter, not caller-managed datasets, graph or side effects.
        """
        self._validate_features(features)
        if (not isinstance(residual_targets, torch.Tensor)
                or residual_targets.device.type != 'cpu' or residual_targets.dtype != torch.float32
                or residual_targets.shape != (features.shape[0], self.output_dim)
                or not bool(torch.isfinite(residual_targets).all())):
            raise ValueError('finite, matching CPU residual targets required')
        if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 10000:
            raise ValueError('steps must be bounded between 1 and 10000')
        if isinstance(lr, bool) or not isinstance(lr, (int, float)) or not math.isfinite(lr) or not 0 < lr <= 1:
            raise ValueError('positive bounded finite learning rate required')
        if (isinstance(orthogonality_weight, bool) or not isinstance(orthogonality_weight, (int, float))
                or not math.isfinite(orthogonality_weight) or orthogonality_weight < 0):
            raise ValueError('nonnegative finite orthogonality penalty required')
        refs = []
        for r in orthogonality_refs:
            if (not isinstance(r, torch.Tensor) or r.device.type != 'cpu'
                    or r.dtype != torch.float32 or r.shape != (self.input_dim, self.output_dim)
                    or not bool(torch.isfinite(r).all())):
                raise ValueError('previous-expert delta must be finite CPU float32')
            refs.append(r.detach().clone())
        state = self.checkpoint()
        optimizer = torch.optim.SGD((self.a, self.b), lr=float(lr))
        try:
            for _ in range(steps):
                optimizer.zero_grad(set_to_none=True)
                prediction = self.forward(features)
                loss = torch.nn.functional.mse_loss(prediction, residual_targets)
                delta = self.a @ self.b
                if orthogonality_weight:
                    for ref in refs:
                        loss = loss + orthogonality_weight * (delta * ref).sum().square()
                if not bool(torch.isfinite(loss)):
                    raise ValueError('nonfinite loss')
                loss.backward()
                if any(p.grad is None or not bool(torch.isfinite(p.grad).all()) for p in (self.a, self.b)):
                    raise ValueError('nonfinite or missing gradient')
                optimizer.step()
                if not bool(torch.isfinite(self.a).all()) or not bool(torch.isfinite(self.b).all()):
                    raise ValueError('nonfinite updated parameter')
            self.last_loss = float(loss.detach())
            return self.last_loss
        except BaseException:
            self.restore(state)
            raise
