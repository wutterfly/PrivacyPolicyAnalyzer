"""Fine-tunes one model for one task on a frozen data split."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch
from datasets import Dataset, Features, Sequence, Value
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from transformers.trainer_callback import PrinterCallback

from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.shared.util import cleanup_memory
from privacy_policy_analyzer.training.config import TrainingConfig
from privacy_policy_analyzer.training.data import (
    LabelSchema,
    Samples,
    Task,
    extract_samples,
    oversample_indices,
    slugify,
)
from privacy_policy_analyzer.training.metrics import (
    compute_metrics,
    find_optimal_thresholds,
    thresholds_array,
)
from privacy_policy_analyzer.training.progress import SimpleProgressBarCallback
from privacy_policy_analyzer.training.split import PARTITIONS, DataSplit
from privacy_policy_analyzer.training.util import get_optimal_precision, set_global_seed

logger = get_logger(__name__)


@dataclass
class TrainResult:
    """Outcome of one ``train`` call."""

    task: Task
    model_name: str
    status: str  # "trained" | "cached" | "skipped"
    results_file: Path | None = None
    metrics: dict | None = None  # test metrics at threshold 0.5
    reason: str | None = None


def results_path(out_dir: Path, task: Task, model_name: str) -> Path:
    return Path(out_dir) / task.path / f"training_results_{slugify(model_name)}.json"


def model_dir(out_dir: Path, task: Task, model_name: str) -> Path:
    return Path(out_dir) / task.path / slugify(model_name)


def run_id(model_name: str, task: Task, config: TrainingConfig, split: DataSplit, schema: LabelSchema) -> str:
    """Identifies a run by everything that determines its result."""

    payload = {
        "model": model_name,
        "task": str(task),
        "labels": task.labels(schema),
        "config": config.to_dict(),
        "split": split.hash,
        "data": split.fingerprint,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _environment() -> dict[str, Any]:
    import datasets
    import sklearn
    import transformers

    env: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "datasets": datasets.__version__,
        "scikit-learn": sklearn.__version__,
        "cuda": torch.version.cuda,
    }
    if torch.cuda.is_available():
        env["gpu"] = torch.cuda.get_device_name(0)
    return env


def _precision_args(config: TrainingConfig, model_name: str) -> dict[str, bool]:
    if config.precision == "auto":
        return get_optimal_precision(model_name)["precision"]
    return {"fp32": {}, "fp16": {"fp16": True}, "bf16": {"bf16": True}}[config.precision]


def _to_dataset(samples: Samples, tokenizer, max_length: int, index: np.ndarray | None = None) -> Dataset:
    if index is not None:
        samples = samples.subset(index)
    features = Features({"text": Value("string"), "labels": Sequence(Value("float32"))})
    dataset = Dataset.from_dict(
        {"text": samples.texts, "labels": samples.labels.tolist()}, features=features
    )
    return dataset.map(
        lambda batch: tokenizer(batch["text"], max_length=max_length, truncation=True, padding=False),
        batched=True,
        remove_columns=["text"],
    )


def _report_support(task: Task, parts: dict[str, Samples], names: list[str]) -> None:
    for partition, samples in parts.items():
        if len(samples) == 0:
            continue
        support = samples.support(names)
        empty = [n for n in names if support[n] == 0 and n != task.fallback]
        if empty:
            logger.warning(
                "%s: %s partition has no positive examples for: %s",
                task, partition, ", ".join(empty),
            )


def train(
    model_name: str,
    task: Task,
    split: DataSplit,
    schema: LabelSchema,
    out_dir: Path,
    config: TrainingConfig = TrainingConfig(),
    force: bool = False,
) -> TrainResult:
    """Trains ``model_name`` on the train partition of ``split`` for ``task``.

    The eval partition selects the best epoch and the per-label thresholds; the
    test partition is only evaluated once, at the end. Results go to
    ``<out_dir>/<task>/training_results_<model>.json`` and the model to
    ``<out_dir>/<task>/<model>/``. A run whose results file carries the same
    ``run_id`` is not repeated unless ``force``.
    """

    out_dir = Path(out_dir)
    label2id = task.label2id(schema)
    names = list(label2id)  # insertion order == id order
    results_file = results_path(out_dir, task, model_name)
    rid = run_id(model_name, task, config, split, schema)

    if results_file.exists() and not force:
        previous = json.loads(results_file.read_text(encoding="utf-8"))
        if previous.get("run_id") == rid:
            logger.info("%s / %s: already trained (run_id=%s), skipping", task, model_name, rid)
            return TrainResult(
                task, model_name, "cached", results_file,
                (previous.get("test_metrics") or {}).get("all", {}).get("at_0.5"),
            )

    parts = {p: extract_samples(split.items(p), task, label2id) for p in PARTITIONS}
    sizes = {p: len(s) for p, s in parts.items()}
    for needed in ("train", "eval"):
        if sizes[needed] == 0:
            reason = f"no {needed} samples for {task} in this split"
            logger.warning("%s / %s: skipped, %s", task, model_name, reason)
            return TrainResult(task, model_name, "skipped", reason=reason)
    _report_support(task, parts, names)

    start = perf_counter()
    cleanup_memory()
    set_global_seed(config.seed, config.deterministic)  # before the head is initialised

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    ratio = config.oversampling if config.oversampling is not None else task.default_oversampling
    train_index = oversample_indices(
        parts["train"].labels, ratio,
        skip=[label2id[task.fallback]], max_copies=config.oversampling_max_copies,
    )
    ds_train = _to_dataset(parts["train"], tokenizer, config.max_length, train_index)
    ds_eval = _to_dataset(parts["eval"], tokenizer, config.max_length)
    ds_test = _to_dataset(parts["test"], tokenizer, config.max_length) if sizes["test"] else None

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(label2id),
        problem_type="multi_label_classification",
        id2label={i: n for n, i in label2id.items()},
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )

    run_dir = model_dir(out_dir, task, model_name)
    run_dir.mkdir(parents=True, exist_ok=True)
    precision = _precision_args(config, model_name)
    args = TrainingArguments(
        output_dir=str(run_dir),
        eval_strategy="epoch",
        # not "best": with it transformers never records best_model_checkpoint, so
        # load_best_model_at_end silently keeps the last epoch instead of the best
        save_strategy="epoch",
        save_total_limit=1,  # keeps the best checkpoint (plus the last one)
        save_only_model=True,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        learning_rate=config.learning_rate,
        num_train_epochs=config.epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.eval_batch_size,
        gradient_accumulation_steps=config.grad_accum_steps,
        weight_decay=config.weight_decay,
        warmup_ratio=config.warmup_ratio,
        optim=config.optim,
        auto_find_batch_size=False,  # would make the batch size depend on free memory
        seed=config.seed,
        data_seed=config.seed,
        dataloader_pin_memory=torch.cuda.is_available(),
        dataloader_num_workers=config.num_workers,
        logging_strategy="no",
        disable_tqdm=True,
        log_level="error",
        report_to="none",
        **precision,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        processing_class=tokenizer,
        compute_metrics=lambda p: compute_metrics(p.predictions, p.label_ids, names),
        callbacks=[SimpleProgressBarCallback(f"{task}/{model_name}")],
    )
    trainer.remove_callback(PrinterCallback)

    logger.info(
        "Training %s on %s: train=%d (%d after oversampling) eval=%d test=%d",
        model_name, task, sizes["train"], len(ds_train), sizes["eval"], sizes["test"],
    )
    trainer.train()

    # eval partition: thresholds; test partition: touched once, here
    eval_out = trainer.predict(ds_eval)
    thresholds = find_optimal_thresholds(eval_out.predictions, eval_out.label_ids, names)
    tuned = thresholds_array(thresholds, names)

    test_metrics: dict[str, dict[str, dict[str, float]]] | None = None
    if ds_test is not None:
        test_logits = trainer.predict(ds_test).predictions
        test_labels = parts["test"].labels
        test_metrics = {}
        subsets = {"all": np.ones(len(test_labels), dtype=bool), "real": ~parts["test"].synthetic}
        for key, mask in subsets.items():
            if mask.any():
                test_metrics[key] = {
                    "at_0.5": compute_metrics(test_logits[mask], test_labels[mask], names),
                    "tuned": compute_metrics(test_logits[mask], test_labels[mask], names, tuned),
                }

    trainer.save_model(str(run_dir))
    for checkpoint in run_dir.glob("checkpoint-*"):  # only the best one was kept; the final model is saved above
        shutil.rmtree(checkpoint, ignore_errors=True)

    final = test_metrics["all"]["at_0.5"] if test_metrics else None
    result = {
        "run_id": rid,
        "model_name": model_name,
        "task": str(task),
        "training_duration": perf_counter() - start,
        "config": config.to_dict(),
        "resolved_precision": precision or "fp32",
        "split": {
            "hash": split.hash,
            "seed": split.seed,
            "ratios": list(split.ratios),
            "data_fingerprint": split.fingerprint,
            "policies": split.policies,
        },
        "sizes": {**sizes, "train_oversampled": len(ds_train)},
        "label_support": {p: s.support(names) for p, s in parts.items()},
        "best_metric": trainer.state.best_metric,
        "eval_metrics": compute_metrics(eval_out.predictions, eval_out.label_ids, names),
        "test_metrics": test_metrics,
        "optimal_thresholds": thresholds,
        "final_metrics": final,  # test, threshold 0.5, real + synthetic sentences
        "environment": _environment(),
    }
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    del model, trainer, ds_train, ds_eval, ds_test, tokenizer
    cleanup_memory()
    return TrainResult(task, model_name, "trained", results_file, final)
