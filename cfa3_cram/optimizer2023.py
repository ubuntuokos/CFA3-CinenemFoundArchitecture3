"""CFA3 CrAM 2023 CPU reference adapter (NOT a runtime-admitted provider).

Algorithmic reference: IST-DASLab/CrAM, pinned at
b89d9ff2b0c7d343736d587dd27f95d86a2df1cf (Apache-2.0).
Independent implementation of the TopkCrAM two-pass optimization pattern;
no vendored upstream code. No Model Router/HRB/Security authority is implemented.
Actual runtime execution requires the external CFA3 admission gates.
"""

from __future__ import annotations

import copy
import math
import random
from collections.abc import Callable, Iterable

try:
    import torch
except ImportError:
    torch = None


UPSTREAM_COMMIT = "b89d9ff2b0c7d343736d587dd27f95d86a2df1cf"


class MissingBackendError(RuntimeError):
    """The optional, explicitly selected CPU PyTorch backend is unavailable."""


class TopkCrAM2023CPU:
    """CPU-only closure optimizer for isolated CrAM 2023 qualification.

    This is an optional Python optimization component, not an authorization
    service and not an application-facing production path. The caller must
    validate model/data rights, resource leases, model routing and workload
    mode through the existing CFA3 authorities before invoking it.

    Expects clean gradients to exist from the first forward/backward pass.
    Runs the closure on a perturbed, temporarily sparsified model, then
    restores original parameters before applying a base SGD update.
    """

    def __init__(
        self,
        parameters: Iterable,
        *,
        lr: float = 0.01,
        rho: float = 0.05,
        sparsities: tuple[float, ...] = (0.5, 0.7, 0.9),
        plus_version: bool = True,
        sparse_grad: bool = True,
        seed: int = 0,
    ) -> None:
        if torch is None:
            raise MissingBackendError("PyTorch CPU backend not installed")
        if not (math.isfinite(lr) and lr > 0 and math.isfinite(rho) and rho >= 0):
            raise ValueError("lr must be positive and rho nonnegative, both finite")
        if not sparsities or any(not math.isfinite(s) or s < 0 or s >= 1 for s in sparsities):
            raise ValueError("sparsities must be nonempty, finite and in [0,1)")
        params = list(parameters)
        if not params:
            raise ValueError("model has no parameters")
        if any(p.device.type != "cpu" for p in params):
            raise MissingBackendError("CrAM 2023 CPU adapter refuses non-CPU parameters")
        if any(not p.is_floating_point() for p in params):
            raise ValueError("parameters must be floating point tensors")
        self._parameters = params
        self.base_optimizer = torch.optim.SGD(params, lr=lr)
        self.rho = rho
        self.sparsities = tuple(sparsities)
        self.plus_version = plus_version
        self.sparse_grad = sparse_grad
        self._rng = random.Random(seed)
        self.last_sparsity: float | None = None

    def zero_grad(self) -> None:
        self.base_optimizer.zero_grad(set_to_none=True)

    def state_dict(self) -> dict:
        return {
            "base_optimizer": self.base_optimizer.state_dict(),
            "rho": self.rho,
            "sparsities": self.sparsities,
            "plus_version": self.plus_version,
            "sparse_grad": self.sparse_grad,
            "rng_state": self._rng.getstate(),
            "last_sparsity": self.last_sparsity,
            "source_commit": UPSTREAM_COMMIT,
        }

    def load_state_dict(self, snapshot: dict) -> None:
        """Restore optimizer/reproducibility state; model tensors are caller-owned."""
        if snapshot.get("source_commit") != UPSTREAM_COMMIT:
            raise ValueError("unverified optimizer source revision")
        if (snapshot.get("rho") != self.rho or
            tuple(snapshot.get("sparsities", ())) != self.sparsities or
            snapshot.get("plus_version") != self.plus_version or
            snapshot.get("sparse_grad") != self.sparse_grad):
            raise ValueError("incompatible checkpoint optimizer configuration")
        self.base_optimizer.load_state_dict(copy.deepcopy(snapshot["base_optimizer"]))
        self._rng.setstate(snapshot["rng_state"])
        self.last_sparsity = snapshot["last_sparsity"]

    def step(self, closure: Callable):
        if not callable(closure):
            raise ValueError("CrAM requires a forward/backward closure")
        old_grads = {p: None if p.grad is None else p.grad.detach().clone() for p in self._parameters}
        if not any(g is not None for g in old_grads.values()):
            raise ValueError("clean backward pass required before CrAM step")
        if any(g is not None and not torch.isfinite(g).all().item() for g in old_grads.values()):
            raise ValueError("non-finite clean gradient")
        if any(p.device.type != "cpu" for p in self._parameters):
            raise MissingBackendError("no implicit accelerator/CPU fallback")
        old_params = {p: p.detach().clone() for p in self._parameters}
        old_optimizer_state = copy.deepcopy(self.base_optimizer.state_dict())
        old_rng_state = self._rng.getstate()
        old_sparsity = self.last_sparsity
        try:
            k = self._rng.choice(self.sparsities)
            masks = {}
            with torch.no_grad():
                for p, grad in old_grads.items():
                    if grad is not None:
                        p.add_(grad, alpha=self.rho)
                # Global threshold for all eligible matrix/conv weights,
                # matching the TopkCrAM group-wise sparsification policy.
                eligible = [p for p in self._parameters if p.ndim > 1 and old_grads[p] is not None]
                if eligible:
                    values = torch.cat([p.detach().abs().reshape(-1).float() for p in eligible])
                    cutoff = torch.quantile(values, k) if k else None
                    for p in eligible:
                        mask = torch.ones_like(p) if cutoff is None else (p.abs() > cutoff).to(p.dtype)
                        masks[p] = mask
                        p.mul_(mask)
            self.zero_grad()
            with torch.enable_grad():
                loss = closure()
            if not isinstance(loss, torch.Tensor) or loss.numel() != 1 or not torch.isfinite(loss.detach()).all().item():
                raise ValueError("closure must return a finite scalar tensor")
            updated_grads = {p: None if p.grad is None else p.grad.detach().clone() for p in self._parameters}
            if any(g is not None and not torch.isfinite(g).all().item() for g in updated_grads.values()):
                raise ValueError("non-finite sparsified gradient")
            with torch.no_grad():
                for p in self._parameters:
                    p.copy_(old_params[p])
                    grad = updated_grads[p]
                    if grad is not None and old_grads[p] is not None:
                        if self.sparse_grad and p in masks:
                            grad.mul_(masks[p])
                        if self.plus_version:
                            grad.add_(old_grads[p])
                        p.grad = grad
                    else:
                        p.grad = None
                self.base_optimizer.step()
            self.last_sparsity = k
            return loss.detach()
        except BaseException:
            with torch.no_grad():
                for p in self._parameters:
                    p.copy_(old_params[p])
                    p.grad = old_grads[p]
            self.base_optimizer.load_state_dict(old_optimizer_state)
            self._rng.setstate(old_rng_state)
            self.last_sparsity = old_sparsity
            raise
