import logging
from logging import info

from privacy_policy_analyzer.crawl import CrawlError

from privacy_policy_analyzer.pipeline import PolicyResult, PipelineManager
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.DEBUG)

    # Analyze directly from URL
    name = "OpenAI"
    url = "https://openai.com/policies/row-privacy-policy/"

    manager = PipelineManager(onnx=False)

    result: PolicyResult | CrawlError = manager.analyze_url(name, url)

    if isinstance(result, PolicyResult):
        info("Analysis Results:")
        info(result.text)
        info(result.structured)
        info(result.analyzed)

        with open("debug_analysis.json", "w", encoding="utf-8") as f:
            import json

            json.dump(result.to_json(), f, ensure_ascii=False, indent=2, default=str)
