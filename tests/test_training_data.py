"""Tasks, multi-hot extraction and oversampling of the training data."""

import numpy as np
import pytest

from privacy_policy_analyzer.shared.annotation import (
    ContentAnnotation,
    RawEntry,
    TopicAnnotation,
)
from privacy_policy_analyzer.training.data import (
    LabelSchema,
    Task,
    build_label2id,
    extract_samples,
    oversample_indices,
    slugify,
)
from privacy_policy_analyzer.training.split import Item

SCHEMA = LabelSchema(
    scope=["Website", "App", "Unspecified"],
    topics=["Retention", "Security/Privacy", "Other"],
    topicContents={"Retention": ["Duration", "Indefinite"], "Security/Privacy": ["Encryption"], "Other": []},
    contentAttributes={},
)


def item(scopes, topics, synthetic=False):
    topic_objs = [
        TopicAnnotation(t, [ContentAnnotation(c, []) for c in contents])
        for t, contents in topics.items()
    ]
    return Item(RawEntry(1, "text", scopes, topic_objs), "file", synthetic)


class TestTask:
    def test_parse(self):
        assert Task.parse("scope") == Task("scope")
        assert Task.parse("content:Security/Privacy") == Task("content", "Security/Privacy")
        assert str(Task("content", "Retention")) == "content:Retention"

    def test_content_needs_topic(self):
        with pytest.raises(ValueError):
            Task("content")
        with pytest.raises(ValueError):
            Task("scope", "Retention")

    def test_all_skips_topics_without_contents(self):
        assert [str(t) for t in Task.all(SCHEMA)] == [
            "scope", "topic", "content:Retention", "content:Security/Privacy",
        ]

    def test_output_path_is_filesystem_safe(self):
        assert Task("content", "Security/Privacy").path.as_posix() == "content/Security_Privacy"
        assert Task("scope").path.as_posix() == "scope"

    def test_fallback_label_comes_first(self):
        assert list(Task("scope").label2id(SCHEMA))[0] == "Unspecified"
        assert list(Task("topic").label2id(SCHEMA))[0] == "Other"

    def test_slugify(self):
        assert slugify("google-bert/bert-base-uncased") == "google-bert_bert-base-uncased"


class TestExtractSamples:
    def test_scope(self):
        l2i = Task("scope").label2id(SCHEMA)
        s = extract_samples([item(["App", "Website"], {})], Task("scope"), l2i)
        assert s.labels[0].tolist() == [0, 1, 1]  # Unspecified, Website, App

    def test_content_only_uses_sentences_with_the_topic(self):
        task = Task("content", "Retention")
        l2i = task.label2id(SCHEMA)
        s = extract_samples(
            [item([], {"Retention": ["Duration"]}), item([], {"Security/Privacy": ["Encryption"]}), item([], {})],
            task, l2i,
        )
        assert len(s) == 1 and s.labels[0, l2i["Duration"]] == 1

    def test_unknown_label_is_a_clear_error(self):
        l2i = Task("scope").label2id(SCHEMA)
        with pytest.raises(ValueError, match="Mars"):
            extract_samples([item(["Mars"], {})], Task("scope"), l2i)

    def test_empty_input(self):
        s = extract_samples([], Task("scope"), Task("scope").label2id(SCHEMA))
        assert s.labels.shape == (0, 3)

    def test_synthetic_flag_is_kept(self):
        l2i = Task("scope").label2id(SCHEMA)
        s = extract_samples([item(["App"], {}), item(["App"], {}, synthetic=True)], Task("scope"), l2i)
        assert s.synthetic.tolist() == [False, True]


class TestOversampling:
    def labels(self):
        # 10 rows of label 0, 2 of label 1, 1 of label 2, none of label 3
        y = np.zeros((10, 4), dtype=np.float32)
        y[:, 0] = 1
        y[:2, 1] = 1
        y[2, 2] = 1
        return y

    def test_original_rows_come_first_and_rare_labels_reach_the_target(self):
        y = self.labels()
        idx = oversample_indices(y, 0.5)
        assert idx[:10].tolist() == list(range(10))
        counts = y[idx].sum(axis=0)
        assert counts[1] >= 5 and counts[2] >= 5  # target = int(10 * 0.5)
        assert counts[3] == 0  # nothing to copy

    def test_deterministic(self):
        y = self.labels()
        assert oversample_indices(y, 0.7).tolist() == oversample_indices(y, 0.7).tolist()

    def test_ratio_zero_changes_nothing(self):
        assert oversample_indices(self.labels(), 0.0).tolist() == list(range(10))

    def test_empty(self):
        assert len(oversample_indices(np.zeros((0, 3), dtype=np.float32), 0.5)) == 0

    def test_skipped_fallback_sets_no_target_and_gets_no_copies(self):
        # label 0 (fallback) is on every row; without it the largest label has 2
        y = self.labels()
        assert oversample_indices(y, 0.5, skip=[0]).tolist() == list(range(10))  # target int(2 * 0.5) = 1
        # a rare fallback is not topped up either
        y = np.zeros((10, 2), dtype=np.float32)
        y[:, 1] = 1
        y[0, 0] = 1
        idx = oversample_indices(y, 1.0, skip=[0])
        assert len(idx) == 10

    def test_copies_count_for_every_label_on_the_row(self):
        # labels 1 and 2 always occur together: topping up one tops up the other
        y = np.zeros((12, 3), dtype=np.float32)
        y[:10, 0] = 1
        y[10:, 1] = 1
        y[10:, 2] = 1
        idx = oversample_indices(y, 0.5)  # target 5
        counts = y[idx].sum(axis=0)
        assert counts[1] == 5 and counts[2] == 5
        assert len(idx) == 15  # 3 copies, not 3 per label

    def test_max_copies_limits_repeats_of_one_row(self):
        y = self.labels()  # label 2 has a single positive row, needs 4 copies for target 5
        idx = oversample_indices(y, 0.5, max_copies=2)
        assert np.bincount(idx).max() <= 3  # original + 2 copies
        assert y[idx].sum(axis=0)[2] == 3  # stays below the target

    def test_rows_with_fewer_labels_are_copied_first(self):
        y = np.zeros((6, 3), dtype=np.float32)
        y[:4, 0] = 1
        y[4, [0, 1]] = 1  # label 1 together with the frequent label 0
        y[5, 1] = 1  # label 1 alone
        idx = oversample_indices(y, 0.75)  # label 0: 5 positives, target 3, label 1 needs one copy
        assert idx[6:].tolist() == [5]


def test_label2id_has_no_duplicates():
    assert build_label2id(["Other", "A", "A"], "Other") == {"Other": 0, "A": 1}
