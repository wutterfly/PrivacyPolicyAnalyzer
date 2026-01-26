import logging

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
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.DEBUG)

    pipeline: Pipeline = Pipeline(
        language=Language.EN,
        model_configs=DEFAULT_MODEL_CONFIGS,
        splitter_configs=EN_SPLITTER_CONFIG,
        pattern_configs=EN_PATTERN_CONFIG,
        duration_pattern_configs=EN_DURATION_PATTERN_CONFIG,
        date_pattern_config=EN_DATE_PATTERN_CONFIG,
        onnx=False,
    )

    name = "OpenAI"
    url = "https://openai.com/policies/row-privacy-policy/"

    # Or analyze directly from URL
    result: PolicyResult | CrawlError = pipeline.run_with_url(name, url, Language.EN)

    if isinstance(result, PolicyResult):
        print("Analysis Results:")
        print(result.text)
        print(result.structured)
        print(result.analyzed)
