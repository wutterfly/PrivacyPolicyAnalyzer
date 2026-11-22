"""Train / eval / test splitting of the annotated corpus.

The corpus has three kinds of files:

* **Policies**: real, annotated privacy policies. Sentences of one policy share
  wording and boilerplate, so with ``by="policy"`` (the default) a policy is kept
  whole in exactly one partition. That keeps near-duplicates from leaking from
  train into eval/test.
* **Synthetic files** (file name contains ``synthesized``): generated sentences
  that do not belong to any policy. They are always split sentence by sentence.
* **Individual files** (file name contains ``individual``): real sentences
  collected one by one from policies that are not in the corpus otherwise. Like
  synthetic sentences they are split sentence by sentence, but they count as
  real (not synthetic) in the reported metrics.

``by="sentence"`` switches to a plain random split of every sentence, real or
synthetic, ignoring which policy it came from (the old behaviour; the test
numbers it gives are optimistic because of the leakage).

With ``stratify=True`` (the default) the sentences that are split one by one
are not shuffled at random but distributed label by label (iterative
stratification, rarest label first), taking into account what the whole
policies already put into each partition. Every label then ends up in train,
eval and test in roughly the split ratios, and a label with at least 3 such
positives in total is guaranteed to be in every partition (2: train and test,
1: train).

The split is computed once for the whole corpus, so every model and every task
(scope, topic, content) sees the same train/eval/test sentences, and it can be
frozen to a JSON manifest so later runs reproduce it exactly. This module has no
torch / datasets dependency.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
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
INDIVIDUAL_MARKER = "individual"
MANIFEST_VERSION = 1

SplitBy = Literal["policy", "sentence"]
Kind = Literal["policy", "synthetic", "individual"]
Ratios = tuple[float, float, float]
DEFAULT_RATIOS: Ratios = (0.7, 0.15, 0.15)
LabelKey = tuple[str, ...]  # ("scope", s) / ("topic", t) / ("content", t, c)


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
    kind: Kind

    @property
    def synthetic(self) -> bool:
        return self.kind == "synthetic"

    @property
    def loose(self) -> bool:
        """Sentences without a policy of their own: always split one by one."""
        return self.kind != "policy"

    def items(self) -> list[Item]:
        return [Item(e, self.name, self.synthetic) for e in self.entries]


@dataclass(frozen=True)
class Corpus:
    documents: list[Document]  # sorted by name
    fingerprint: str  # sha256 over the data files (names + bytes)

    @property
    def policies(self) -> list[Document]:
        return [d for d in self.documents if not d.loose]

    @property
    def loose(self) -> list[Document]:
        """Synthetic and individual files."""
        return [d for d in self.documents if d.loose]

    @property
    def synthetic(self) -> list[Document]:
        return [d for d in self.documents if d.synthetic]


def _kind(name: str, synthetic_marker: str, individual_marker: str) -> Kind:
    lowered = name.lower()
    if synthetic_marker in lowered:
        return "synthetic"
    if individual_marker in lowered:
        return "individual"
    return "policy"


def label_keys(entry: RawEntry) -> frozenset[LabelKey]:
    """Every label of a sentence over all tasks: scopes, topics and contents."""

    keys: set[LabelKey] = {("scope", s) for s in entry.scopes}
    for t in entry.topics:
        keys.add(("topic", t.topic))
        keys.update(("content", t.topic, c.content) for c in t.contents)
    return frozenset(keys)


def _fingerprint(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(folder.glob("*.json"), key=lambda p: p.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        # normalise line endings so a git checkout on Windows hashes the same
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return digest.hexdigest()


def load_corpus(
    folder: Path,
    synthetic_marker: str = SYNTHETIC_MARKER,
    individual_marker: str = INDIVIDUAL_MARKER,
) -> Corpus:
    """Loads every annotated file in ``folder`` (sorted, so order is stable)."""

    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Training data folder does not exist: {folder}")

    n_files = len(list(folder.glob("*.json")))
    documents = [
        Document(name, entries, _kind(name, synthetic_marker, individual_marker))
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
    if not any(not d.loose for d in documents):
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
    stratify: bool = False  # sentences were distributed label by label, not at random
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
        how = "stratified" if self.stratify else "random"
        return f"by {self.by}, {how}; " + "; ".join(parts)

    # -- persistence ---------------------------------------------------------

    def to_dict(self) -> dict:
        d = {
            "version": MANIFEST_VERSION,
            "seed": self.seed,
            "ratios": list(self.ratios),
            "by": self.by,
            "data_fingerprint": self.fingerprint,
            "policies": self.policies,
            "sentences": self.sentences,
        }
        # only written when set, so manifests (and hashes) of random splits stay
        # exactly as they were before stratification existed
        if self.stratify:
            d["stratify"] = True
        return d

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
            stratify=bool(raw.get("stratify", False)),
        )


def _materialize(
    corpus: Corpus,
    seed: int,
    ratios: Ratios,
    by: SplitBy,
    policies: dict[str, list[str]],
    sentences: dict[str, dict[str, list[int]]],
    stratify: bool = False,
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
            if doc.loose:
                raise ValueError(f"{name} is {doc.kind} and cannot be assigned as a policy")
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
        stratify=stratify,
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


def _label_floors(n: int, ratios: Ratios, min_per_label: int) -> dict[str, int]:
    """Least number of positives every partition should get for a label with
    ``n`` positives in total: train first, then test, then eval, and eval/test
    never more than train."""

    floors = {p: 0 for p in PARTITIONS}
    if min_per_label <= 0 or n == 0:
        return floors
    if n <= 2:
        floors["train"] = 1
        if n == 2:
            floors["test"] = 1
    else:
        m = min(min_per_label, n // 3)
        floors = {p: m for p in PARTITIONS}
    return {p: (v if ratios[i] > 0 else 0) for i, (p, v) in enumerate(floors.items())}


def _stratified_split(
    pool: list[Item],
    ratios: Ratios,
    rng: random.Random,
    assigned: dict[str, list[Item]],
    min_per_label: int,
) -> dict[str, list[Item]]:
    """Distributes ``pool`` label by label (iterative stratification, Sechidis
    et al. 2011), counting the sentences in ``assigned`` (whole policies) too.

    The label with the fewest unplaced sentences goes first; each of its
    sentences goes to the partition that is furthest below its floor (see
    ``_label_floors``), otherwise to the one furthest below its share of that
    label, ties broken by the free room in the partition, then at random.
    """

    if not pool:
        return {p: [] for p in PARTITIONS}
    labels = [label_keys(i.entry) for i in pool]
    have = {p: Counter(k for i in assigned[p] for k in label_keys(i.entry)) for p in PARTITIONS}
    total = Counter(k for ks in labels for k in ks)
    for p in PARTITIONS:
        total.update(have[p])
    share = {p: {k: n * ratios[i] for k, n in total.items()} for i, p in enumerate(PARTITIONS)}
    floors = {k: _label_floors(n, ratios, min_per_label) for k, n in total.items()}
    room = dict(zip(PARTITIONS, map(float, _partition_sizes(len(pool), ratios))))
    floor_order = {"train": 2, "test": 1, "eval": 0}  # who gets a missing floor first

    remaining = Counter(k for ks in labels for k in ks)
    order = list(range(len(pool)))
    rng.shuffle(order)
    unplaced = set(order)
    out: dict[str, list[Item]] = {p: [] for p in PARTITIONS}

    def place(idx: int, p: str) -> None:
        out[p].append(pool[idx])
        have[p].update(labels[idx])
        remaining.subtract(labels[idx])
        room[p] -= 1
        unplaced.discard(idx)

    def choose(key: LabelKey | None) -> str:
        active = [p for i, p in enumerate(PARTITIONS) if ratios[i] > 0]
        if key is None:  # sentence without any label
            return max(active, key=lambda p: (room[p], rng.random()))
        missing = {p: floors[key][p] - have[p][key] for p in active}
        needy = [p for p in active if missing[p] > 0]
        if needy:
            return max(needy, key=lambda p: (missing[p], floor_order[p]))
        return max(active, key=lambda p: (share[p][key] - have[p][key], room[p], rng.random()))

    while unplaced:
        open_keys = [k for k, n in remaining.items() if n > 0]
        if not open_keys:
            for idx in [i for i in order if i in unplaced]:
                place(idx, choose(None))
            break
        key = min(open_keys, key=lambda k: (remaining[k], k))
        for idx in [i for i in order if i in unplaced and key in labels[i]]:
            place(idx, choose(key))
    return out


def make_split(
    corpus: Corpus,
    seed: int = 42,
    ratios: Ratios = DEFAULT_RATIOS,
    by: SplitBy = "policy",
    stratify: bool = True,
    min_per_label: int = 1,
) -> DataSplit:
    """Splits the corpus deterministically from ``seed``.

    ``by="policy"``: real policies are shuffled and assigned whole; synthetic and
    individual sentences are pooled and split sentence by sentence.
    ``by="sentence"``: every sentence of every file is split individually.
    Both use the same ratios. ``stratify`` distributes the sentences that are
    split one by one label by label instead of at random (the policies are
    assigned the same way either way); ``min_per_label`` is the least number of
    positives per label and partition that stratification aims for (see
    ``_label_floors``).
    """

    ratios = tuple(ratios)  # type: ignore[assignment]
    _validate_ratios(ratios)  # type: ignore[arg-type]
    if by not in ("policy", "sentence"):
        raise ValueError(f"Unknown split mode: {by!r}")
    rng = random.Random(seed)

    policies: dict[str, list[str]] = {p: [] for p in PARTITIONS}
    whole: dict[str, list[Item]] = {p: [] for p in PARTITIONS}
    if by == "policy":
        names = [d.name for d in corpus.policies]  # already sorted
        chunks = _split_pool(names, ratios, rng)  # type: ignore[arg-type]
        policies = {p: sorted(chunks[p]) for p in PARTITIONS}
        by_name = {d.name: d for d in corpus.documents}
        whole = {p: [i for n in policies[p] for i in by_name[n].items()] for p in PARTITIONS}
        loose = corpus.loose
    else:
        loose = corpus.documents

    if stratify:
        items = [i for d in loose for i in d.items()]
        placed = _stratified_split(items, ratios, rng, whole, min_per_label)  # type: ignore[arg-type]
        chunks = {p: [(i.source, i.entry.line_number) for i in placed[p]] for p in PARTITIONS}
    else:
        pool = [(d.name, e.line_number) for d in loose for e in d.entries]
        chunks = _split_pool(pool, ratios, rng)  # type: ignore[arg-type]
    sentences: dict[str, dict[str, list[int]]] = {}
    for p, chunk in chunks.items():
        per_file: dict[str, list[int]] = {}
        for name, line in sorted(chunk):
            per_file.setdefault(name, []).append(line)
        sentences[p] = per_file

    return _materialize(corpus, seed, ratios, by, policies, sentences, stratify)  # type: ignore[arg-type]


def prepare_split(
    corpus: Corpus,
    manifest: Path | None,
    seed: int = 42,
    ratios: Ratios = DEFAULT_RATIOS,
    resplit: bool = False,
    by: SplitBy = "policy",
    stratify: bool = True,
) -> DataSplit:
    """Returns the frozen split from ``manifest``, creating it on first use.

    A manifest that was written with a different seed, ratios, split mode or
    stratification is an error (rather than silently reused), unless ``resplit``
    is set. Manifests from before stratification existed count as not stratified.
    """

    ratios = tuple(ratios)  # type: ignore[assignment]
    if manifest is not None and Path(manifest).exists() and not resplit:
        split = DataSplit.load(Path(manifest), corpus)
        made = (split.seed, tuple(split.ratios), split.by, split.stratify)
        if made != (seed, ratios, by, stratify):
            raise ValueError(
                f"{manifest} was made with seed={split.seed} ratios={tuple(split.ratios)} "
                f"by={split.by} stratify={split.stratify}, but seed={seed} ratios={ratios} "
                f"by={by} stratify={stratify} was requested. "
                "Use the same settings, resplit=True / --resplit, or another output folder."
            )
        logger.info("Using frozen split from %s", manifest)
    else:
        split = make_split(corpus, seed, ratios, by, stratify)  # type: ignore[arg-type]
        if manifest is not None:
            split.save(Path(manifest))
            logger.info("Wrote split manifest to %s", manifest)

    logger.info("Split (%s): %s", split.hash, split.summary())
    return split
