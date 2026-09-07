import logging
from logging import info

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.config import EN_DEFAULT_CONFIGURATION
from privacy_policy_analyzer.crawl import CrawlError
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.INFO)

    pipeline: Pipeline = Pipeline(
        config=EN_DEFAULT_CONFIGURATION,
        onnx=False,
        cache_load_models=True,
    )

    name = "Eufy"
    url = "https://security-app.eufylife.com/v1/overall/termsof?type=privacypolicy_us"

    # Or analyze directly from URL
    result: PolicyResult | CrawlError = pipeline.run_with_url(name, url, Language.EN)

    if isinstance(result, PolicyResult):
        with open("debug_analysis.json", "w", encoding="utf-8") as f:
            import json

            json.dump(result.to_json(), f, ensure_ascii=False, indent=2, default=str)
