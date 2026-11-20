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
