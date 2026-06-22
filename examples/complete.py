import json
import logging
from logging import info

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.analysis import DEFAULT_MODEL_CONFIGS
from privacy_policy_analyzer.crawl import CrawlError
from privacy_policy_analyzer.patterns.en import (
    EN_DATE_PATTERN_CONFIG,
    EN_DURATION_PATTERN_CONFIG,
    EN_PATTERN_CONFIG,
    EN_SPLITTER_CONFIG,
)
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult
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

    pipeline: Pipeline = Pipeline(
        language=Language.EN,
        model_configs=DEFAULT_MODEL_CONFIGS,
        splitter_configs=EN_SPLITTER_CONFIG,
        pattern_configs=EN_PATTERN_CONFIG,
        duration_pattern_configs=EN_DURATION_PATTERN_CONFIG,
        date_pattern_config=EN_DATE_PATTERN_CONFIG,
        email_pattern_config=None,
        onnx=False,
        cache_load_models=True,
    )

    name = "OpenAI"
    url = "https://openai.com/policies/row-privacy-policy/"

    # Or analyze directly from URL
    policy: PolicyResult | CrawlError = pipeline.run_with_url(name, url, Language.EN)

    if isinstance(policy, PolicyResult):
        info("Analysis Results:")
        info(policy.text)
        info(policy.structured)
        info(policy.analyzed)

        with open("debug_analysis.json", "w", encoding="utf-8") as f:
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
        with open("summary_report.json", "w", encoding="utf-8") as f:
            json.dump(summary.to_json(), f, ensure_ascii=False, indent=2, default=str)

        # Generate and print score report
        scores = create_score_report(summary)
        info(scores)

        # Calculate and print readability scores
        readability = calculate_readability_scores(policy.text)
        info(f"Readability Scores: {readability}")

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
        label_svg = generate_svg_label(scores, summary, readability, policy.source)
        with open("label.svg", "w", encoding="utf-8") as f:
            f.write(label_svg)
        info("Label SVG saved as label.svg")
