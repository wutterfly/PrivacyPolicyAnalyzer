import json
import logging
from logging import info

from privacy_policy_analyzer.crawl import CrawlError

from privacy_policy_analyzer.pipeline import PolicyResult, PipelineManager
from privacy_policy_analyzer.report.detailed import create_detailed_report
from privacy_policy_analyzer.report.flow import generate_context_map, generate_topic_map
from privacy_policy_analyzer.report.label import generate_svg_label
from privacy_policy_analyzer.report.readability import calculate_readability_scores
from privacy_policy_analyzer.report.score import create_score_report
from privacy_policy_analyzer.report.summary import create_summary_report
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.DEBUG)
    set_logging(level=logging.DEBUG, include_timestamp=True, file="debug_analysis.log")

    # Analyze directly from URL
    name = "OpenAI"
    url = "https://openai.com/policies/row-privacy-policy/"

    manager = PipelineManager(onnx=False)

    policy: PolicyResult | CrawlError = manager.analyze_url(name, url)
    
    if isinstance(policy, PolicyResult):
        info("Analysis Results:")
        info(policy.text)
        info(policy.structured)
        info(policy.analyzed)

        with open("debug_analysis2g.json", "w", encoding="utf-8") as f:
            json.dump(policy.to_json(), f, ensure_ascii=False, indent=2, default=str)

        include_contexts: list[str] = []
        exclude_contexts: list[str] = []

        # Generate and print detailed report
        detailed = create_detailed_report(
            policy.analyzed, include_contexts, exclude_contexts
        )
        info(detailed)

        # Generate and print summary report
        summary = create_summary_report(
            policy.analyzed, include_contexts, exclude_contexts
        )
        info(summary)
        with open("summary_report2g.json", "w", encoding="utf-8") as f:
            json.dump(summary.to_json(), f, ensure_ascii=False, indent=2, default=str)

        # Generate and print score report
        scores = create_score_report(summary)
        info(scores)

        # Calculate and print readability scores
        readability = calculate_readability_scores(policy.text)
        info(f"Readability Scores: {readability}")

        # Generate and save topic map PNG
        topic_map_png = generate_topic_map(policy.analyzed)
        with open("topic_map2g.png", "wb") as f:
            f.write(topic_map_png)
        info("Topic map PNG saved as topic_map.svg")

        context_map_png = generate_context_map(policy.analyzed)
        with open("context_map2.png", "wb") as f:
            f.write(context_map_png)
        info("Context map PNG saved as context_map.png")

        # Generate and save label SVG
        label_svg = generate_svg_label(scores, summary, readability, policy.source)
        with open("label2g.svg", "w", encoding="utf-8") as f:
            f.write(label_svg)
        info("Label SVG saved as label.svg")
