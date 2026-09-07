import json
import logging

from privacy_policy_analyzer import UnsupportedLanguage
from privacy_policy_analyzer.analysis.err import ModelLoadError
from privacy_policy_analyzer.config import DEFAULT_CONFIGURATIONS
from privacy_policy_analyzer.crawl import CrawlError
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.INFO, file="debug_analysis.log")

    pipeline: Pipeline = Pipeline(
        configs=DEFAULT_CONFIGURATIONS,
        prefer_onnx=False,
        cache_load_models=True,
    )

    name = "Eufy"
    url = "https://security-app.eufylife.com/v1/overall/termsof?type=privacypolicy_us"

    # Or analyze directly from URL
    result: PolicyResult | CrawlError | UnsupportedLanguage | ModelLoadError = (
        pipeline.run_with_url(name, url, None)
    )

    if not isinstance(result, PolicyResult):
        print(f"Analysis failed for {name}: {result}")

    elif isinstance(result, PolicyResult):
        with open("debug_analysis.json", "w", encoding="utf-8") as f:
            json.dump(result.to_json(), f, ensure_ascii=False, indent=2, default=str)
