import logging

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.config import DEFAULT_CONFIGURATIONS
from privacy_policy_analyzer.crawl import CrawlError
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult, UnsupportedLanguage
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.INFO, file="debug_analysis.log")

    pipeline: Pipeline = Pipeline(
        configs=DEFAULT_CONFIGURATIONS,
        onnx=False,
        cache_load_models=True,
    )

    name = "Eufy"
    # url = "https://security-app.eufylife.com/v1/overall/termsof?type=privacypolicy_us"
    url = "https://www.bahn.de/datenschutz"

    # Or analyze directly from URL
    result: PolicyResult | CrawlError | UnsupportedLanguage = pipeline.run_with_url(
        name, url, Language.EN
    )

    if isinstance(result, CrawlError):
        print(f"Error occurred while crawling: {result}")
    elif isinstance(result, UnsupportedLanguage):
        print(f"Unsupported language: {result.language}")

    if isinstance(result, PolicyResult):
        with open("debug_analysis.json", "w", encoding="utf-8") as f:
            import json

            json.dump(result.to_json(), f, ensure_ascii=False, indent=2, default=str)
