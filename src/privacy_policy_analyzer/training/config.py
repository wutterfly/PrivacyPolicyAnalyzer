"""Hyperparameters of a training run."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class TrainingConfig:
    """Everything that influences a run besides the data split, the model and the task.

    Defaults match the values the previous hard-coded trainer used, except where
    noted. Two runs with equal config, split, model and task give the same model
    (on the same hardware and library versions).
    """

    seed: int = 42
    epochs: int = 10
    learning_rate: float = 5e-5
    batch_size: int = 16
    grad_accum_steps: int = 2
    eval_batch_size: int = 32
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    max_length: int = 512
    # Oversampling of rare labels in the training partition, as a fraction of the
    # most frequent label's count (the fallback label is left out). None: 0.5 for
    # scope/topic, 0.7 for content.
    oversampling: float | None = None
    # At most this many extra copies of one sentence; None: no limit. Keeps labels
    # with only a handful of examples from being repeated dozens of times.
    oversampling_max_copies: int | None = 5
    # "auto" picks bf16 / fp16 / fp32 from the GPU. Fix it for runs across machines.
    precision: Literal["auto", "fp32", "fp16", "bf16"] = "auto"
    # The old trainer asked for 8-bit AdamW (bitsandbytes). Plain AdamW needs no
    # extra dependency and behaves the same on every platform.
    optim: str = "adamw_torch"
    # Deterministic GPU kernels (slower). Without it runs can differ on a GPU.
    deterministic: bool = True
    # 0 keeps data loading in-process, which is deterministic and fast enough
    # for sentence-sized data.
    num_workers: int = 0

    def to_dict(self) -> dict:
        return asdict(self)
