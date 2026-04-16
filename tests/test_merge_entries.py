from privacy_policy_analyzer.analysis.post_processing import (
    ContentAnnotation,
    SkipRule,
    StructuredEntry,
    TopicAnnotation,
    merge_entries,
)
from privacy_policy_analyzer.analysis.structure import (
    Text,
)

dst = StructuredEntry(
    text="We use cookies to track your activity on our website.",
    structure=Text(1),
    contexts=["Website"],
    topics=[
        TopicAnnotation(
            topic="Processing",
            contents=[
                ContentAnnotation(
                    content="Tracking/Conversion", attributes=["Cookies"]
                ),
            ],
        ),
    ],
)

src = StructuredEntry(
    text="We also use web beacons and share data with Google Analytics.",
    structure=Text(1),
    contexts=["App"],
    topics=[
        TopicAnnotation(
            topic="Processing",
            contents=[
                ContentAnnotation(
                    content="Tracking/Conversion", attributes=["WebBeacons"]
                ),
            ],
        ),
        TopicAnnotation(
            topic="ThirdParty",
            contents=[
                ContentAnnotation(content="Company", attributes=["Google"]),
            ],
        ),
        TopicAnnotation(
            topic="Purpose",
            contents=[
                ContentAnnotation(content="Analytics", attributes=[]),
            ],
        ),
    ],
)


def test_contexts_merged():
    result = merge_entries(dst, src)
    assert set(result.contexts) == {"Website", "App"}


def test_dst_text_preserved():
    result = merge_entries(dst, src)
    assert result.text == dst.text


def test_dst_structure_preserved():
    result = merge_entries(dst, src)
    assert result.structure == dst.structure


def test_tracking_attributes_merged():
    # Both entries mention Tracking/Conversion — attributes should be combined
    result = merge_entries(dst, src)
    processing = next(tpc for tpc in result.topics if tpc.topic == "Processing")
    tracking = next(
        cnt for cnt in processing.contents if cnt.content == "Tracking/Conversion"
    )
    assert set(tracking.attributes) == {"Cookies", "WebBeacons"}


def test_new_topic_added():
    # ThirdParty and Purpose only exist in src — should appear in result
    result = merge_entries(dst, src)
    topic_names = {tpc.topic for tpc in result.topics}
    assert "ThirdParty" in topic_names
    assert "Purpose" in topic_names


def test_third_party_company_attribute():
    result = merge_entries(dst, src)
    third_party = next(tpc for tpc in result.topics if tpc.topic == "ThirdParty")
    company = next(cnt for cnt in third_party.contents if cnt.content == "Company")
    assert "Google" in company.attributes


def test_dst_not_mutated():
    merge_entries(dst, src)
    assert dst.contexts == ["Website"]
    assert len(dst.topics) == 1


def test_src_not_mutated():
    merge_entries(dst, src)
    assert src.contexts == ["App"]
    assert len(src.topics) == 3


def test_skip_third_party_topic():
    result = merge_entries(dst, src, skips=[SkipRule(topic="ThirdParty")])
    assert all(tpc.topic != "ThirdParty" for tpc in result.topics)


def test_skip_specific_tracking_attribute():
    # Skip WebBeacons content from being merged in
    result = merge_entries(
        dst,
        src,
        skips=[SkipRule(topic="Processing", contents=["Tracking/Conversion"])],
    )
    processing = next(tpc for tpc in result.topics if tpc.topic == "Processing")
    tracking = next(
        cnt for cnt in processing.contents if cnt.content == "Tracking/Conversion"
    )
    # Only dst's original Cookies attribute should remain
    assert set(tracking.attributes) == {"Cookies"}
