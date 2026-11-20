"""Train / eval / test splitting of the annotated corpus.

The corpus has two kinds of files:

* **Policies**: real, annotated privacy policies. Sentences of one policy share
  wording and boilerplate, so with ``by="policy"`` (the default) a policy is kept
  whole in exactly one partition. That keeps near-duplicates from leaking from
  train into eval/test.
* **Synthetic files** (file name contains ``synthesized``): generated sentences
  that do not belong to any policy. They are always split sentence by sentence.

``by="sentence"`` switches to a plain random split of every sentence, real or
synthetic, ignoring which policy it came from (the old behaviour; the test
numbers it gives are optimistic because of the leakage).

The split is computed once for the whole corpus, so every model and every task
(scope, topic, content) sees the same train/eval/test sentences, and it can be
frozen to a JSON manifest so later runs reproduce it exactly. This module has no
torch / datasets dependency.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Literal

from privacy_policy_analyzer.shared.annotation import (
    RawEntry,
    read_training_documents,
)
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)

PARTITIONS = ("train", "eval", "test")
SYNTHETIC_MARKER = "synthesized"
MANIFEST_VERSION = 1

SplitBy = Literal["policy", "sentence"]
Ratios = tuple[float, float, float]
DEFAULT_RATIOS: Ratios = (0.7, 0.15, 0.15)


@dataclass(frozen=True)
class Item:
    """One annotated sentence together with where it came from."""

    entry: RawEntry
    source: str  # file stem, e.g. "17__Wyze Cam v3"
    synthetic: bool


@dataclass(frozen=True)
class Document:
    name: str  # file stem
    entries: list[RawEntry]
    synthetic: bool

    def items(self) -> list[Item]:
        return [Item(e, self.name, self.synthetic) for e in self.entries]


@dataclass(frozen=True)
class Corpus:
    documents: list[Document]  # sorted by name
    fingerprint: str  # sha256 over the data files (names + bytes)

    @property
    def policies(self) -> list[Document]:
        return [d for d in self.documents if not d.synthetic]

    @property
    def synthetic(self) -> list[Document]:
        return [d for d in self.documents if d.synthetic]


def _fingerprint(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(folder.glob("*.json"), key=lambda p: p.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        # normalise line endings so a git checkout on Windows hashes the same
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return digest.hexdigest()


def load_corpus(folder: Path, synthetic_marker: str = SYNTHETIC_MARKER) -> Corpus:
    """Loads every annotated file in ``folder`` (sorted, so order is stable)."""

    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Training data folder does not exist: {folder}")

    n_files = len(list(folder.glob("*.json")))
    documents = [
        Document(name, entries, synthetic_marker in name.lower())
        for name, entries in read_training_documents(folder)
    ]
    if len(documents) != n_files:
        raise ValueError(
            f"{n_files - len(documents)} file(s) in {folder} could not be read; "
            "see the log above. Refusing to train on a partial corpus."
        )
    for doc in documents:
        lines = [e.line_number for e in doc.entries]
        if len(set(lines)) != len(lines):
            raise ValueError(f"{doc.name}: line_number values are not unique")
    if not any(not d.synthetic for d in documents):
        raise ValueError(f"No real policies found in {folder}")
    return Corpus(documents, _fingerprint(folder))


def _partition_sizes(n: int, ratios: Ratios) -> tuple[int, int, int]:
    """Splits ``n`` units into (train, eval, test) counts by largest remainder.

    Every partition with a positive ratio gets at least one unit (if ``n`` is
    large enough); the train partition absorbs the rest.
    """

    quotas = [n * r for r in ratios]
    counts = [int(q) for q in quotas]
    order = sorted(range(3), key=lambda i: (-(quotas[i] - counts[i]), i))
    for i in order[: n - sum(counts)]:
        counts[i] += 1
    for i in (1, 2):  # eval, test must not be empty
        if ratios[i] > 0 and counts[i] == 0 and counts[0] > 1:
            counts[i] += 1
            counts[0] -= 1
    return counts[0], counts[1], counts[2]


def _validate_ratios(ratios: Ratios) -> None:
    if len(ratios) != 3 or any(r < 0 for r in ratios) or ratios[0] <= 0:
        raise ValueError(f"Invalid split ratios: {ratios}")
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise ValueError(f"Split ratios must sum to 1, got {sum(ratios)}")


@dataclass
class DataSplit:
    """The frozen assignment of policies and synthetic sentences to partitions."""

    seed: int
    ratios: Ratios
    by: SplitBy
    fingerprint: str
    policies: dict[str, list[str]]  # partition -> policies assigned whole (empty if by="sentence")
    sentences: dict[str, dict[str, list[int]]]  # partition -> file -> line numbers assigned one by one
    _items: dict[str, list[Item]] = field(default_factory=dict, repr=False)

    def items(self, partition: str) -> list[Item]:
        return self._items[partition]

    def real_items(self, partition: str) -> list[Item]:
        return [i for i in self._items[partition] if not i.synthetic]

    def __iter__(self) -> Iterator[tuple[str, list[Item]]]:
        for p in PARTITIONS:
            yield p, self._items[p]

    @property
    def hash(self) -> str:
        """Identifies the exact assignment (not the data behind it)."""
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

    def summary(self) -> str:
        parts = []
        for p in PARTITIONS:
            real = len(self.real_items(p))
            synthetic = len(self._items[p]) - real
            where = f"{len(self.policies[p])} policies/" if self.by == "policy" else ""
            parts.append(f"{p}: {where}{real} real + {synthetic} synthetic sentences")
        return f"by {self.by}; " + "; ".join(parts)

    # -- persistence ---------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": MANIFEST_VERSION,
            "seed": self.seed,
            "ratios": list(self.ratios),
            "by": self.by,
            "data_fingerprint": self.fingerprint,
            "policies": self.policies,
            "sentences": self.sentences,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=1, ensure_ascii=False)

    @staticmethod
    def load(path: Path, corpus: Corpus) -> DataSplit:
        """Rebuilds a frozen split against ``corpus``.

        Fails if the data files changed since the split was written, since the
        recorded assignment would then no longer describe the same sentences.
        """

        with Path(path).open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if raw.get("version") != MANIFEST_VERSION:
            raise ValueError(f"{path}: unsupported split manifest version")
        if raw["data_fingerprint"] != corpus.fingerprint:
            raise ValueError(
                f"{path}: the annotated data changed since this split was made. "
                "Re-split (resplit=True / --resplit) or use a new output folder."
            )
        return _materialize(
            corpus,
            seed=raw["seed"],
            ratios=tuple(raw["ratios"]),  # type: ignore[arg-type]
            by=raw["by"],
            policies=raw["policies"],
            sentences={p: raw["sentences"][p] for p in PARTITIONS},
        )



def _materialize(
    corpus: Corpus,
    seed: int,
    ratios: Ratios,
    by: SplitBy,
    policies: dict[str, list[str]],
    sentences: dict[str, dict[str, list[int]]],
) -> DataSplit:
    """Builds a ``DataSplit`` and checks that every sentence of the corpus is in
    exactly one partition."""

    if by not in ("policy", "sentence"):
        raise ValueError(f"Unknown split mode: {by!r}")
    by_name = {d.name: d for d in corpus.documents}
    items: dict[str, list[Item]] = {p: [] for p in PARTITIONS}
    seen: dict[str, int] = {}  # document -> number of sentences placed

    for p in PARTITIONS:
        for name in policies[p]:
            doc = by_name[name]
            if doc.synthetic:
                raise ValueError(f"{name} is synthetic and cannot be assigned as a policy")
            items[p].extend(doc.items())
            seen[name] = seen.get(name, 0) + len(doc.entries)
        for name, lines in sentences[p].items():
            wanted = set(lines)
            picked = [i for i in by_name[name].items() if i.entry.line_number in wanted]
            if len(picked) != len(lines):
                raise ValueError(f"Split refers to unknown sentences of {name}")
            items[p].extend(picked)
            seen[name] = seen.get(name, 0) + len(picked)

    for doc in corpus.documents:
        if seen.get(doc.name, 0) != len(doc.entries):
            raise ValueError(f"Split does not place every sentence of {doc.name} exactly once")

    return DataSplit(
        seed=seed,
        ratios=ratios,
        by=by,
        fingerprint=corpus.fingerprint,
        policies={p: list(policies[p]) for p in PARTITIONS},
        sentences={p: {k: list(v) for k, v in sentences[p].items()} for p in PARTITIONS},
        _items=items,
    )


def _split_pool(pool: list, ratios: Ratios, rng: random.Random) -> dict[str, list]:
    rng.shuffle(pool)
    n_train, n_eval, _ = _partition_sizes(len(pool), ratios)
    return {
        "train": pool[:n_train],
        "eval": pool[n_train : n_train + n_eval],
        "test": pool[n_train + n_eval :],
    }


def make_split(
    corpus: Corpus,
    seed: int = 42,
    ratios: Ratios = DEFAULT_RATIOS,
    by: SplitBy = "policy",
) -> DataSplit:
    """Splits the corpus deterministically from ``seed``.

    ``by="policy"``: real policies are shuffled and assigned whole; synthetic
    sentences are pooled over all synthetic files and split sentence by sentence.
    ``by="sentence"``: every sentence of every file is split individually.
    Both use the same ratios.
    """

    ratios = tuple(ratios)  # type: ignore[assignment]
    _validate_ratios(ratios)  # type: ignore[arg-type]
    if by not in ("policy", "sentence"):
        raise ValueError(f"Unknown split mode: {by!r}")
    rng = random.Random(seed)

    policies: dict[str, list[str]] = {p: [] for p in PARTITIONS}
    if by == "policy":
        names = [d.name for d in corpus.policies]  # already sorted
        chunks = _split_pool(names, ratios, rng)  # type: ignore[arg-type]
        policies = {p: sorted(chunks[p]) for p in PARTITIONS}
        loose = corpus.synthetic
    else:
        loose = corpus.documents

    pool = [(d.name, e.line_number) for d in loose for e in d.entries]
    chunks = _split_pool(pool, ratios, rng)  # type: ignore[arg-type]
    sentences: dict[str, dict[str, list[int]]] = {}
    for p, chunk in chunks.items():
        per_file: dict[str, list[int]] = {}
        for name, line in sorted(chunk):
            per_file.setdefault(name, []).append(line)
        sentences[p] = per_file

    return _materialize(corpus, seed, ratios, by, policies, sentences)  # type: ignore[arg-type]


def prepare_split(
    corpus: Corpus,
    manifest: Path | None,
    seed: int = 42,
    ratios: Ratios = DEFAULT_RATIOS,
    resplit: bool = False,
    by: SplitBy = "policy",
) -> DataSplit:
    """Returns the frozen split from ``manifest``, creating it on first use.

    A manifest that was written with a different seed, ratios or split mode is an
    error (rather than silently reused), unless ``resplit`` is set.
    """

    ratios = tuple(ratios)  # type: ignore[assignment]
    if manifest is not None and Path(manifest).exists() and not resplit:
        split = DataSplit.load(Path(manifest), corpus)
        if (split.seed, tuple(split.ratios), split.by) != (seed, ratios, by):
            raise ValueError(
                f"{manifest} was made with seed={split.seed} ratios={tuple(split.ratios)} "
                f"by={split.by}, but seed={seed} ratios={ratios} by={by} was requested. "
                "Use the same settings, resplit=True / --resplit, or another output folder."
            )
        logger.info("Using frozen split from %s", manifest)
    else:
        split = make_split(corpus, seed, ratios, by)  # type: ignore[arg-type]
        if manifest is not None:
            split.save(Path(manifest))
            logger.info("Wrote split manifest to %s", manifest)

    logger.info("Split (%s): %s", split.hash, split.summary())
    return split
