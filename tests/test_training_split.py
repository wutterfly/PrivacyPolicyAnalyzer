"""Train / eval / test splitting: by policy or by sentence, reproducible, frozen."""

import json
from pathlib import Path

import pytest

from privacy_policy_analyzer.training.split import (
    PARTITIONS,
    DataSplit,
    load_corpus,
    make_split,
    prepare_split,
)


def write_file(folder: Path, name: str, n: int) -> None:
    entries = [
        {
            "line_number": i,
            "text": f"{name} sentence {i}",
            "annotations": {"scopes": ["Unspecified"], "scopeSpecifics": {}, "topics": []},
        }
        for i in range(n)
    ]
    (folder / f"{name}.json").write_text(json.dumps(entries), encoding="utf-8")


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    for i in range(10):
        write_file(tmp_path, f"{i}__policy", 5 + i * 3)  # different sizes
    write_file(tmp_path, "999__synthesized", 40)
    write_file(tmp_path, "9999__synthesized", 30)
    return tmp_path


def sentence_ids(split: DataSplit, partition: str) -> set[tuple[str, int]]:
    return {(i.source, i.entry.line_number) for i in split.items(partition)}


class TestPolicySplit:
    def test_policies_are_never_shared_between_partitions(self, folder):
        split = make_split(load_corpus(folder), seed=1)
        for p in PARTITIONS:
            real_sources = {i.source for i in split.real_items(p)}
            assert real_sources == set(split.policies[p])
        used = [n for p in PARTITIONS for n in split.policies[p]]
        assert len(used) == len(set(used)) == 10

    def test_ten_policies_split_7_2_1(self, folder):
        split = make_split(load_corpus(folder))
        assert [len(split.policies[p]) for p in PARTITIONS] == [7, 2, 1]

    def test_synthetic_sentences_are_split_sentence_wise(self, folder):
        split = make_split(load_corpus(folder))
        for p in PARTITIONS:
            assert any(i.synthetic for i in split.items(p))
        # same synthetic file shows up in several partitions
        files_per_partition = [set(split.sentences[p]) for p in PARTITIONS]
        assert all("999__synthesized" in f for f in files_per_partition)

    def test_every_sentence_is_in_exactly_one_partition(self, folder):
        corpus = load_corpus(folder)
        split = make_split(corpus)
        all_ids = [x for p in PARTITIONS for x in sentence_ids(split, p)]
        assert len(all_ids) == len(set(all_ids)) == sum(len(d.entries) for d in corpus.documents)


class TestSentenceSplit:
    def test_policies_are_spread_over_partitions(self, folder):
        split = make_split(load_corpus(folder), by="sentence")
        assert all(split.policies[p] == [] for p in PARTITIONS)
        sources = [{i.source for i in split.real_items(p)} for p in PARTITIONS]
        assert len(sources[0] & sources[2]) > 0  # leakage, which is what this mode means

    def test_every_sentence_is_in_exactly_one_partition(self, folder):
        corpus = load_corpus(folder)
        split = make_split(corpus, by="sentence")
        all_ids = [x for p in PARTITIONS for x in sentence_ids(split, p)]
        assert len(all_ids) == len(set(all_ids)) == sum(len(d.entries) for d in corpus.documents)

    def test_ratios_are_followed(self, folder):
        corpus = load_corpus(folder)
        total = sum(len(d.entries) for d in corpus.documents)
        split = make_split(corpus, by="sentence")
        sizes = [len(split.items(p)) for p in PARTITIONS]
        assert abs(sizes[0] / total - 0.7) < 0.01
        assert abs(sizes[1] / total - 0.15) < 0.01

    def test_modes_give_different_splits(self, folder):
        corpus = load_corpus(folder)
        assert make_split(corpus, by="policy").hash != make_split(corpus, by="sentence").hash

    def test_unknown_mode_is_rejected(self, folder):
        with pytest.raises(ValueError):
            make_split(load_corpus(folder), by="paragraph")  # type: ignore[arg-type]


class TestReproducibility:
    @pytest.mark.parametrize("by", ["policy", "sentence"])
    def test_same_seed_same_split(self, folder, by):
        corpus = load_corpus(folder)
        assert make_split(corpus, 7, by=by).hash == make_split(corpus, 7, by=by).hash

    def test_other_seed_other_split(self, folder):
        corpus = load_corpus(folder)
        assert make_split(corpus, 1).hash != make_split(corpus, 2).hash

    def test_independent_of_file_listing_order(self, folder, tmp_path_factory):
        other = tmp_path_factory.mktemp("copy")
        for path in sorted(folder.glob("*.json"), reverse=True):
            (other / path.name).write_bytes(path.read_bytes())
        a, b = load_corpus(folder), load_corpus(other)
        assert a.fingerprint == b.fingerprint
        assert make_split(a).hash == make_split(b).hash

    def test_crlf_does_not_change_fingerprint(self, folder, tmp_path_factory):
        other = tmp_path_factory.mktemp("crlf")
        for path in folder.glob("*.json"):
            (other / path.name).write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        assert load_corpus(folder).fingerprint == load_corpus(other).fingerprint


class TestManifest:
    @pytest.mark.parametrize("by", ["policy", "sentence"])
    def test_roundtrip(self, folder, tmp_path, by):
        corpus = load_corpus(folder)
        split = make_split(corpus, by=by)
        split.save(tmp_path / "split.json")
        loaded = DataSplit.load(tmp_path / "split.json", corpus)
        assert loaded.hash == split.hash and loaded.by == by
        for p in PARTITIONS:
            assert sentence_ids(loaded, p) == sentence_ids(split, p)

    def test_prepare_creates_then_reuses(self, folder, tmp_path):
        corpus = load_corpus(folder)
        manifest = tmp_path / "out" / "split.json"
        first = prepare_split(corpus, manifest)
        assert manifest.exists()
        assert prepare_split(corpus, manifest).hash == first.hash

    def test_changed_data_is_refused(self, folder, tmp_path):
        manifest = tmp_path / "split.json"
        prepare_split(load_corpus(folder), manifest)
        write_file(folder, "0__policy", 99)
        with pytest.raises(ValueError, match="changed"):
            prepare_split(load_corpus(folder), manifest)

    @pytest.mark.parametrize(
        "kwargs", [{"seed": 1}, {"ratios": (0.8, 0.1, 0.1)}, {"by": "sentence"}]
    )
    def test_different_settings_are_refused_unless_resplit(self, folder, tmp_path, kwargs):
        corpus = load_corpus(folder)
        manifest = tmp_path / "split.json"
        prepare_split(corpus, manifest)
        with pytest.raises(ValueError, match="resplit"):
            prepare_split(corpus, manifest, **kwargs)
        again = prepare_split(corpus, manifest, resplit=True, **kwargs)
        assert prepare_split(corpus, manifest, **kwargs).hash == again.hash


def labeled(line: int, text: str, scope: str = "Unspecified", content: tuple[str, str] | None = None) -> dict:
    topics = [] if content is None else [
        {"topic": content[0], "contents": [{"content": content[1], "attributes": []}]}
    ]
    return {
        "line_number": line,
        "text": text,
        "annotations": {"scopes": [scope], "scopeSpecifics": {}, "topics": topics},
    }


def write_entries(folder: Path, name: str, entries: list[dict]) -> None:
    (folder / f"{name}.json").write_text(json.dumps(entries), encoding="utf-8")


def positives(split: DataSplit, partition: str, topic: str, content: str) -> int:
    return sum(
        any(t.topic == topic and any(c.content == content for c in t.contents) for t in i.entry.topics)
        for i in split.items(partition)
    )


@pytest.fixture
def rare_folder(tmp_path: Path) -> Path:
    """Ten plain policies, one policy with a label no other policy has, and a
    synthetic file with rare labels among many unlabeled sentences."""

    for i in range(10):
        write_file(tmp_path, f"{i}__policy", 10)
    write_entries(tmp_path, "10__policy", [
        labeled(n, f"owner {n}", content=("Policy", "ResponsiblePerson")) for n in range(6)
    ])
    entries = [labeled(n, f"plain {n}") for n in range(200)]
    rare = {"Three": 3, "Two": 2, "One": 1, "Five": 5}
    line = 200
    for content, n in rare.items():
        for _ in range(n):
            entries.append(labeled(line, f"{content} {line}", content=("Deletion", content)))
            line += 1
    write_entries(tmp_path, "999__synthesized", entries)
    return tmp_path


class TestStratifiedSplit:
    @pytest.mark.parametrize("seed", range(10))
    def test_rare_labels_reach_every_partition(self, rare_folder, seed):
        split = make_split(load_corpus(rare_folder), seed=seed)
        counts = lambda c: [positives(split, p, "Deletion", c) for p in PARTITIONS]
        assert all(n >= 1 for n in counts("Three")) and sum(counts("Three")) == 3
        assert all(n >= 1 for n in counts("Five"))
        assert counts("Two") == [1, 0, 1]  # train and test
        assert counts("One") == [1, 0, 0]  # train

    def test_random_split_misses_rare_labels_for_some_seed(self, rare_folder):
        corpus = load_corpus(rare_folder)
        misses = [
            seed for seed in range(10)
            if any(positives(make_split(corpus, seed=seed, stratify=False), p, "Deletion", "Three") == 0
                   for p in PARTITIONS)
        ]
        assert misses  # which is what stratification is for

    def test_policies_are_assigned_as_without_stratification(self, rare_folder):
        corpus = load_corpus(rare_folder)
        assert make_split(corpus).policies == make_split(corpus, stratify=False).policies

    def test_ratios_are_kept(self, rare_folder):
        corpus = load_corpus(rare_folder)
        split = make_split(corpus, by="sentence")
        total = sum(len(d.entries) for d in corpus.documents)
        sizes = [len(split.items(p)) / total for p in PARTITIONS]
        assert sizes == pytest.approx([0.7, 0.15, 0.15], abs=0.02)

    def test_whole_policies_are_taken_into_account(self, tmp_path):
        # 10__policy is the only policy with ResponsiblePerson; individual sentences
        # with it should fill the partitions that policy is not in
        for i in range(10):
            write_file(tmp_path, f"{i}__policy", 10)
        write_entries(tmp_path, "10__policy", [
            labeled(n, f"owner {n}", content=("Policy", "ResponsiblePerson")) for n in range(20)
        ])
        write_entries(tmp_path, "00000_individual", [
            labeled(n, f"person {n}", content=("Policy", "ResponsiblePerson")) for n in range(6)
        ] + [labeled(100 + n, f"plain {n}") for n in range(30)])
        split = make_split(load_corpus(tmp_path), seed=3)
        holder = next(p for p in PARTITIONS if "10__policy" in split.policies[p])
        for p in PARTITIONS:
            if p != holder:
                assert positives(split, p, "Policy", "ResponsiblePerson") >= 3

    def test_every_sentence_is_in_exactly_one_partition(self, rare_folder):
        corpus = load_corpus(rare_folder)
        for by in ("policy", "sentence"):
            split = make_split(corpus, by=by)
            all_ids = [x for p in PARTITIONS for x in sentence_ids(split, p)]
            assert len(all_ids) == len(set(all_ids)) == sum(len(d.entries) for d in corpus.documents)

    def test_same_seed_same_split(self, rare_folder):
        corpus = load_corpus(rare_folder)
        assert make_split(corpus, 5).hash == make_split(corpus, 5).hash
        assert make_split(corpus, 5).hash != make_split(corpus, 6).hash


class TestIndividualFile:
    def test_is_split_by_sentence_and_counts_as_real(self, folder):
        write_entries(folder, "00000_individual", [labeled(n, f"found {n}") for n in range(40)])
        corpus = load_corpus(folder)
        doc = next(d for d in corpus.documents if d.name == "00000_individual")
        assert doc.kind == "individual" and doc.loose and not doc.synthetic
        assert doc not in corpus.policies
        split = make_split(corpus)
        for p in PARTITIONS:
            assert "00000_individual" not in split.policies[p]
            assert any(i.source == "00000_individual" for i in split.real_items(p))

    def test_cannot_be_assigned_as_a_policy(self, folder, tmp_path):
        write_entries(folder, "00000_individual", [labeled(n, f"found {n}") for n in range(5)])
        corpus = load_corpus(folder)
        split = make_split(corpus)
        raw = split.to_dict()
        raw["policies"]["train"].append("00000_individual")
        (tmp_path / "split.json").write_text(json.dumps(raw), encoding="utf-8")
        with pytest.raises(ValueError, match="individual"):
            DataSplit.load(tmp_path / "split.json", corpus)


class TestStratifyManifest:
    def test_roundtrip_keeps_stratify(self, rare_folder, tmp_path):
        corpus = load_corpus(rare_folder)
        split = make_split(corpus)
        split.save(tmp_path / "split.json")
        loaded = DataSplit.load(tmp_path / "split.json", corpus)
        assert loaded.stratify and loaded.hash == split.hash

    def test_random_split_manifest_has_no_stratify_key(self, rare_folder):
        # keeps manifests and hashes of earlier (random) splits unchanged
        assert "stratify" not in make_split(load_corpus(rare_folder), stratify=False).to_dict()

    def test_old_manifest_is_not_stratified_and_is_refused_for_stratified_run(self, rare_folder, tmp_path):
        corpus = load_corpus(rare_folder)
        manifest = tmp_path / "split.json"
        make_split(corpus, stratify=False).save(manifest)
        assert prepare_split(corpus, manifest, stratify=False).stratify is False
        with pytest.raises(ValueError, match="stratify"):
            prepare_split(corpus, manifest)


class TestEdgeCases:
    def test_bad_ratios(self, folder):
        corpus = load_corpus(folder)
        with pytest.raises(ValueError):
            make_split(corpus, ratios=(0.5, 0.5, 0.5))
        with pytest.raises(ValueError):
            make_split(corpus, ratios=(0.0, 0.5, 0.5))

    def test_unreadable_file_is_an_error(self, folder):
        (folder / "broken.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError, match="could not be read"):
            load_corpus(folder)

    def test_no_policies_is_an_error(self, tmp_path):
        write_file(tmp_path, "999__synthesized", 10)
        with pytest.raises(ValueError, match="No real policies"):
            load_corpus(tmp_path)


class TestLabelFingerprint:
    """A frozen split survives edits of fields training does not read."""

    @pytest.fixture
    def labeled_folder(self, tmp_path: Path) -> Path:
        for i in range(10):
            write_entries(tmp_path, f"{i}__policy", [
                labeled(n, f"{i} sentence {n}", scope="Device", content=("Deletion", "DataType")) for n in range(6)
            ])
        write_entries(tmp_path, "999__synthesized", [labeled(n, f"synthetic {n}") for n in range(30)])
        return tmp_path

    def edit(self, folder: Path, change) -> None:
        path = folder / "3__policy.json"
        entries = json.loads(path.read_text(encoding="utf-8"))
        change(entries[2]["annotations"])
        path.write_text(json.dumps(entries), encoding="utf-8")

    @pytest.mark.parametrize("change", [
        lambda a: a["topics"][0]["contents"][0].update(attributes=["PreciseGeolocation"]),
        lambda a: a.update(scopeSpecifics={"Device": ["Camera"]}),
    ])
    def test_unused_fields_keep_the_split(self, labeled_folder, tmp_path_factory, change):
        manifest = tmp_path_factory.mktemp("out") / "split.json"
        first = prepare_split(load_corpus(labeled_folder), manifest)
        before = load_corpus(labeled_folder)
        self.edit(labeled_folder, change)
        after = load_corpus(labeled_folder)
        assert after.fingerprint != before.fingerprint
        assert after.label_fingerprint == before.label_fingerprint
        again = prepare_split(after, manifest)
        for p in PARTITIONS:
            assert sentence_ids(again, p) == sentence_ids(first, p)

    @pytest.mark.parametrize("change", [
        lambda a: a["topics"][0]["contents"][0].update(content="WeakDeletion"),
        lambda a: a.update(scopes=["App"]),
        lambda a: a.update(topics=[]),
    ])
    def test_label_changes_are_refused(self, labeled_folder, tmp_path_factory, change):
        manifest = tmp_path_factory.mktemp("out") / "split.json"
        prepare_split(load_corpus(labeled_folder), manifest)
        self.edit(labeled_folder, change)
        with pytest.raises(ValueError, match="changed"):
            prepare_split(load_corpus(labeled_folder), manifest)

    def test_manifest_without_label_fingerprint_stays_strict(self, labeled_folder, tmp_path_factory):
        manifest = tmp_path_factory.mktemp("out") / "split.json"
        split = prepare_split(load_corpus(labeled_folder), manifest)
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        assert raw["label_fingerprint"] == split.label_fingerprint
        del raw["label_fingerprint"]
        manifest.write_text(json.dumps(raw), encoding="utf-8")
        # an older manifest loads unchanged, with the same hash
        assert DataSplit.load(manifest, load_corpus(labeled_folder)).hash == split.hash
        self.edit(labeled_folder, lambda a: a["topics"][0]["contents"][0].update(attributes=["X"]))
        with pytest.raises(ValueError, match="changed"):
            DataSplit.load(manifest, load_corpus(labeled_folder))
