import json
import logging

from privacy_policy_analyzer.pipeline import PolicyResult
from privacy_policy_analyzer.report.label import generate_svg_label
from privacy_policy_analyzer.report.readability import calculate_readability_scores
from privacy_policy_analyzer.report.score import create_score_report
from privacy_policy_analyzer.report.summary import create_summary_report
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.DEBUG)

    policy_json: dict = {}
    with open("debug_analysis.json", "r", encoding="utf-8") as f:
        policy_json = json.load(f)

    # Assuming `policy_result` is an instance of `PolicyResult` obtained from analysis
    policy: PolicyResult = PolicyResult.from_json(policy_json)

    include_contexts: list[str] = []
    exclude_contexts: list[str] = []

    # Generate and print summary report
    summary = create_summary_report(policy.analyzed, include_contexts, exclude_contexts)

    with open("summary_report.json", "w", encoding="utf-8") as f:
        json.dump(summary.to_json(), f, indent=2)

    # Generate and print score report
    scores = create_score_report(summary)

    # Calculate and print readability scores
    readability = calculate_readability_scores(policy.text)

    # Generate and save label SVG
    label_svg = generate_svg_label(scores, summary, readability, policy.source)
    with open("label.svg", "w", encoding="utf-8") as f:
        f.write(label_svg)
