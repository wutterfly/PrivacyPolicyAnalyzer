import logging

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.crawl import CollectedPolicy, CrawlError, crawl
from privacy_policy_analyzer.patterns.en import EN_SPLITTER_CONFIG
from privacy_policy_analyzer.shared.logging import set_logging

if __name__ == "__main__":
    set_logging(level=logging.DEBUG)

    url = "https://openai.com/policies/row-privacy-policy/"
    name = "OpenAI"

    result: CollectedPolicy | CrawlError = crawl(
        name, url, Language.EN, EN_SPLITTER_CONFIG
    )

    if isinstance(result, CollectedPolicy):
        print(f"Successfully crawled policy for {name} at {url}")
        print("Extracted Text:")
        print(result.text)
        print(result.structured)
