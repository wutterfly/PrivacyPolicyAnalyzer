import logging
from logging import info

from privacy_policy_analyzer.pipeline import PolicyResult
from privacy_policy_analyzer.report.detailed import create_detailed_report
from privacy_policy_analyzer.report.flow import generate_context_map, generate_topic_map
from privacy_policy_analyzer.report.label import generate_svg_label
from privacy_policy_analyzer.report.score import create_score_report
from privacy_policy_analyzer.report.summary import create_summary_report
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.DEBUG)

    # Assuming `policy_result` is an instance of `PolicyResult` obtained from analysis
    policy: PolicyResult = ...  # Replace with actual PolicyResult object

    include_contexts: list[str] = []
    exclude_contexts: list[str] = []

    # Generate and print detailed report
    detailed = create_detailed_report(
        policy.analyzed, include_contexts, exclude_contexts
    )
    info(detailed)

    # Generate and print summary report
    summary = create_summary_report(policy.analyzed, include_contexts, exclude_contexts)
    info(summary)

    # Generate and print score report
    scores = create_score_report(summary)
    info(scores)

    # Generate and save topic map PNG
    topic_map_png = generate_topic_map(policy.analyzed)
    with open("topic_map.png", "wb") as f:
        f.write(topic_map_png)
    info("Topic map PNG saved as topic_map.svg")

    context_map_png = generate_context_map(policy.analyzed)
    with open("context_map.png", "wb") as f:
        f.write(context_map_png)
    info("Context map PNG saved as context_map.png")

    # Generate and save label SVG
    label_svg = generate_svg_label(scores, summary, policy.source)
    with open("label.svg", "w", encoding="utf-8") as f:
        f.write(label_svg)
    info("Label SVG saved as label.svg")
