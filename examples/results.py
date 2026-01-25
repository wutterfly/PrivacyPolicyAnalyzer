from privacy_policy_analyzer.pipeline import PolicyResult
from privacy_policy_analyzer.report.detailed import create_detailed_report
from privacy_policy_analyzer.report.flow import generate_topic_map
from privacy_policy_analyzer.report.label import generate_svg_label
from privacy_policy_analyzer.report.score import create_score_report
from privacy_policy_analyzer.report.summary import create_summary_report

if __name__ == "__main__":
    # Assuming `policy_result` is an instance of `PolicyResult` obtained from analysis
    policy: PolicyResult = ...  # Replace with actual PolicyResult object

    include_contexts: list[str] = []
    exclude_contexts: list[str] = []

    # Generate and print detailed report
    detailed = create_detailed_report(
        policy.analyzed, include_contexts, exclude_contexts
    )
    print(detailed)

    # Generate and print summary report
    summary = create_summary_report(policy.analyzed, include_contexts, exclude_contexts)
    print(summary)

    # Generate and print score report
    scores = create_score_report(summary)
    assert scores is not None
    print(scores)

    # Generate and save topic map SVG
    topic_map_png = generate_topic_map(policy.analyzed)
    with open("topic_map.png", "wb") as f:
        f.write(topic_map_png)
    print("Topic map SVG saved as topic_map.svg")

    # Generate and save label SVG
    label_svg = generate_svg_label(scores, summary, policy.source)
    with open("label.svg", "w", encoding="utf-8") as f:
        f.write(label_svg)
    print("Label SVG saved as label.svg")
