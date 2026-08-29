import json
import logging
from calendar import c
from logging import info
from pathlib import Path

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


def compute_results(
    out_folder: Path,
    include_contexts: list[str],
    exclude_contexts: list[str],
    policy: PolicyResult,
):

    out_folder.mkdir(parents=True, exist_ok=True)
    info(f"Saving results to {out_folder.resolve()}")

    with open(out_folder / "debug_analysis.json", "w", encoding="utf-8") as f:
        json.dump(policy.to_json(), f, ensure_ascii=False, indent=2, default=str)

    # Generate and print detailed report
    detailed = create_detailed_report(
        policy.analyzed, include_contexts, exclude_contexts
    )

    # Generate and print summary report
    summary = create_summary_report(policy.analyzed, include_contexts, exclude_contexts)

    with open(out_folder / "summary_report.json", "w", encoding="utf-8") as f:
        json.dump(summary.to_json(), f, ensure_ascii=False, indent=2, default=str)

    # Generate and print score report
    scores = create_score_report(summary)

    # Calculate and print readability scores
    readability = calculate_readability_scores(policy.text)

    # Generate and save topic map PNG
    topic_map_png = generate_topic_map(policy.analyzed)
    with open(out_folder / "topic_map.png", "wb") as f:
        f.write(topic_map_png)

    context_map_png = generate_context_map(policy.analyzed)
    with open(out_folder / "context_map.png", "wb") as f:
        f.write(context_map_png)

    # Generate and save label SVG
    label_svg = generate_svg_label(scores, summary, readability, policy.source)
    with open(out_folder / "label.svg", "w", encoding="utf-8") as f:
        f.write(label_svg)


if __name__ == "__main__":
    set_logging(level=logging.INFO, include_timestamp=True, file="debug_analysis.log")

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

    names = ["Gardena", "Eufy", "Wyze"]
    urls = [
        "https://privacyportal.husqvarnagroup.com/en/privacy-notice",
        "https://security-app.eufylife.com/v1/overall/termsof?type=privacypolicy_us",
        "https://www.wyze.com/policies/privacy-policy",
    ]

    for i in range(len(names)):
        name = names[i]
        url = urls[i]

        output_folder: Path = Path(f"./output/{name}/")
        output_folder.mkdir(parents=True, exist_ok=True)

        # Or analyze directly from URL
        policy: PolicyResult | CrawlError = pipeline.run_with_url(
            name, url, Language.EN
        )

        if isinstance(policy, PolicyResult):
            with open(
                output_folder / "debug_analysis.json", "w", encoding="utf-8"
            ) as f:
                json.dump(
                    policy.to_json(), f, ensure_ascii=False, indent=2, default=str
                )

            ###################### Website

            include_contexts: list[str] = ["Website", "Other"]
            exclude_contexts: list[str] = [
                "Store",
                "App",
                "Recruiting",
                "Device",
                "Account",
                "Communication",
            ]

            compute_results(
                output_folder / Path("website/"),
                include_contexts,
                exclude_contexts,
                policy,
            )

            ###################### Device

            include_contexts: list[str] = ["Device", "Other"]
            exclude_contexts: list[str] = [
                "Store",
                "App",
                "Recruiting",
                "Website",
                "Account",
                "Communication",
            ]

            compute_results(
                output_folder / Path("device/"),
                include_contexts,
                exclude_contexts,
                policy,
            )

            ###################### Store

            include_contexts: list[str] = ["Store", "Other"]
            exclude_contexts: list[str] = [
                "App",
                "Recruiting",
                "Website",
                "Account",
                "Communication",
                "Device",
            ]

            compute_results(
                output_folder / Path("store/"),
                include_contexts,
                exclude_contexts,
                policy,
            )

            ###################### App

            include_contexts: list[str] = ["App", "Other"]
            exclude_contexts: list[str] = [
                "Store",
                "Recruiting",
                "Website",
                "Account",
                "Communication",
                "Device",
            ]

            compute_results(
                output_folder / Path("app/"),
                include_contexts,
                exclude_contexts,
                policy,
            )
