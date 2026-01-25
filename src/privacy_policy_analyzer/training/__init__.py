import json
from dataclasses import dataclass
from logging import info
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

import numpy as np
from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    hamming_loss,
    precision_score,
    recall_score,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from transformers.trainer_callback import PrinterCallback

from privacy_policy_analyzer.shared.annotation import (
    RawEntry,
)
from privacy_policy_analyzer.shared.util import cleanup_memory, get_device
from privacy_policy_analyzer.training.data import (
    _build_label2id_map,
    extract_training_data_content,
    extract_training_data_context,
    extract_training_data_topics,
    oversample_minority_labels,
    split_dataset,
)
from privacy_policy_analyzer.training.progress import SimpleProgressBarCallback
from privacy_policy_analyzer.training.util import (
    get_optimal_precision,
)

# Metrics


def _compute_metrics(eval_pred, label_names: list[str], threshold=0.5) -> dict:
    logits, labels = eval_pred
    predictions = 1 / (1 + np.exp(-logits))  # Sigmoid
    predictions = (predictions > threshold).astype(int)  # Threshold

    metrics = {
        "f1_micro": f1_score(
            labels, predictions, average="micro", zero_division=np.nan
        ),
        "f1_macro": f1_score(
            labels, predictions, average="macro", zero_division=np.nan
        ),
        "f1_weighted": f1_score(
            labels, predictions, average="weighted", zero_division=np.nan
        ),
        "precision_micro": precision_score(
            labels, predictions, average="micro", zero_division=np.nan
        ),
        "precision_macro": precision_score(
            labels, predictions, average="macro", zero_division=np.nan
        ),
        "recall_micro": recall_score(
            labels, predictions, average="micro", zero_division=np.nan
        ),
        "recall_macro": recall_score(
            labels, predictions, average="macro", zero_division=np.nan
        ),
        "accuracy": accuracy_score(labels, predictions),
        "hamming_loss": hamming_loss(labels, predictions),
    }

    # Per-label F1 (no averaging)
    f1_per_label = f1_score(labels, predictions, average=None, zero_division=np.nan)
    assert isinstance(f1_per_label, np.ndarray)

    # Add each label's F1 score
    for i, label_name in enumerate(label_names):
        metrics[f"f1_{label_name}"] = f1_per_label[i]

    return metrics


def _find_optimal_thresholds(
    trainer: Trainer,
    eval_dataset: Dataset,
    label_names: list[str],
    metric: Literal["f1_macro", "f1_micro"] = "f1_macro",
) -> dict[str, float]:
    predictions = trainer.predict(eval_dataset)
    logits = predictions.predictions
    probs = 1 / (1 + np.exp(-logits))  # Sigmoid
    labels = predictions.label_ids
    assert isinstance(labels, np.ndarray)

    thresholds = np.arange(0.1, 0.95, 0.05)
    optimal_thresholds = {}

    for i, label_name in enumerate(label_names):
        if labels[:, i].sum() == 0:
            optimal_thresholds[label_name] = 0.5
            continue

        # Vectorized: compute all predictions at once
        preds_all = (
            probs[:, i, np.newaxis] > thresholds
        )  # shape: (n_samples, n_thresholds)

        # Compute F1 for all thresholds
        f1_scores: np.ndarray
        if metric == "f1_macro":
            f1_scores = np.array(
                [
                    f1_score(
                        labels[:, i],
                        preds_all[:, j],
                        average="macro",
                        zero_division=np.nan,
                    )
                    for j in range(len(thresholds))
                ]
            )
        else:  # f1_micro
            f1_scores = np.array(
                [
                    f1_score(
                        labels[:, i],
                        preds_all[:, j],
                        average="micro",
                        zero_division=np.nan,
                    )
                    for j in range(len(thresholds))
                ]
            )

        best_idx = np.argmax(f1_scores)
        optimal_thresholds[label_name] = float(thresholds[best_idx])

    return optimal_thresholds


def _get_compute_metrics(label_names: list[str], threshold=0.5):
    return lambda eval_pred: _compute_metrics(eval_pred, label_names, threshold)


# Model Training Function


def _train_model_on_dataset(
    dataset: Dataset,
    label2id: dict[str, int],
    model_name: str,
    output_dir: Path,
    test_eval_split: float,
    oversampling_ratio: float,
    seed: int,
):
    cleanup_memory()
    start = perf_counter()
    model_output_dir = output_dir / Path(model_name.replace("/", "_"))
    model_output_dir.mkdir(parents=True, exist_ok=True)

    # Label mappings
    id2label = {v: k for k, v in label2id.items()}

    # Split and over-sample
    train, eval = split_dataset(dataset, test_size=test_eval_split, seed=seed)
    train = oversample_minority_labels(train, ratio=oversampling_ratio)
    train = train.shuffle(seed=seed)
    eval = eval.shuffle(seed=seed)

    # Tokenization
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_function(examples) -> dict:
        return tokenizer(
            examples["text"], max_length=512, truncation=True, padding=False
        )

    tokenized_train = train.map(tokenize_function, batched=True)
    tokenized_eval = eval.map(tokenize_function, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Model Initialization
    device = get_device()
    info(f"Using device: {device}")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(label2id),
        problem_type="multi_label_classification",
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    ).to(device)

    # Training Configuration
    config = get_optimal_precision()
    training_args = TrainingArguments(
        output_dir=str(model_output_dir),
        eval_strategy="epoch",
        save_strategy="best",
        save_total_limit=1,
        save_only_model=True,
        learning_rate=5e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        gradient_accumulation_steps=2,
        auto_find_batch_size=True,
        num_train_epochs=10,
        weight_decay=0.01,
        warmup_ratio=0.1,
        **config["precision"],
        # fp16=True,
        # bf16=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        optim="adamw_bnb_8bit",
        dataloader_pin_memory=device == "cuda",
        dataloader_num_workers=4,
        torch_empty_cache_steps=True,
        load_best_model_at_end=True,
        seed=seed,
        data_seed=seed,
        #
        logging_strategy="no",
        logging_steps=None,
        logging_first_step=False,
        disable_tqdm=True,  # Disable progress bars
        log_level="error",
        report_to="none",
    )

    # Trainer Initialization
    label_names = [k for k in label2id.keys()]
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=data_collator,
        compute_metrics=_get_compute_metrics(label_names, threshold=0.5),
        callbacks=[
            SimpleProgressBarCallback(str(model_output_dir)),
        ],
    )
    trainer.remove_callback(PrinterCallback)

    # Training & Evaluation
    info(f"Starting training for model: {model_name} with target: {output_dir}")
    trainer.train()
    final_metrics = trainer.evaluate()

    # Find optimal thresholds
    optimal_thresholds = _find_optimal_thresholds(trainer, tokenized_eval, label_names)

    end = perf_counter()

    # Save final model
    trainer.save_model(str(model_output_dir))

    results_file = output_dir / Path(
        f"training_results_{model_name.replace('/', '_')}.json"
    )
    with results_file.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "model_name": model_name,
                "training_duration": end - start,
                "final_metrics": final_metrics,
                "optimal_thresholds": optimal_thresholds,
            },
            f,
            indent=2,
        )

    # Cleanup
    del model
    del trainer
    del data_collator
    del tokenized_train
    del tokenized_eval
    del dataset
    del tokenizer
    cleanup_memory()


# Training Configuration and Execution


@dataclass
class ModelTrainingConfig:
    """Configuration for training a model."""

    model_name: str
    output_dir: Path
    training_files: list[list[RawEntry]]
    labels: list[str]
    scope: Literal["context", "topic", "content"]
    content_topic: str | None
    test_eval_split: float
    oversampling_ratio: float
    seed: int

    def execute_training(self):
        """Execute the training based on the configuration."""

        # load label2id mapping
        label2id = _build_label2id_map(self.labels)

        # extract dataset based on scope
        dataset: Dataset | None = None
        if self.scope == "context":
            dataset = extract_training_data_context(self.training_files, label2id)
        elif self.scope == "topic":
            dataset = extract_training_data_topics(self.training_files, label2id)
        else:  # content
            assert self.content_topic is not None
            dataset = extract_training_data_content(
                self.training_files, label2id, self.content_topic
            )

        assert dataset is not None
        info(f"Training dataset size: {len(dataset)} samples.")
        _train_model_on_dataset(
            dataset=dataset,
            label2id=label2id,
            model_name=self.model_name,
            output_dir=self.output_dir,
            test_eval_split=self.test_eval_split,
            oversampling_ratio=self.oversampling_ratio,
            seed=self.seed,
        )


def get_label_distribution(
    data: list[RawEntry] | list[list[RawEntry]],
) -> dict[str, Any]:
    """Get label distribution from the training data."""

    combined: list[RawEntry] = []

    if isinstance(data, list) and all(isinstance(i, list) for i in data):
        for sublist in data:
            assert isinstance(sublist, list)
            combined.extend(sublist)
        data = combined
    elif isinstance(data, list) and all(isinstance(i, RawEntry) for i in data):
        for entry in data:
            assert isinstance(entry, RawEntry)
            combined.append(entry)

    else:
        assert False, "Invalid data for label distribution."

    contexts: dict[str, int] = {}
    topics: dict[str, int] = {}
    contents: dict[str, dict[str, int]] = {}

    for entry in combined:
        for ctx in entry.contexts:
            contexts[ctx] = contexts.get(ctx, 0) + 1

        for tpc in entry.topics:
            topics[tpc.topic] = topics.get(tpc.topic, 0) + 1
            for cnt in tpc.contents:
                contents[tpc.topic] = contents.get(tpc.topic, {})
                contents[tpc.topic][cnt.content] = (
                    contents[tpc.topic].get(cnt.content, 0) + 1
                )

    return {
        "len": len(combined),
        "contexts": contexts,
        "topics": topics,
        "contents": contents,
    }
