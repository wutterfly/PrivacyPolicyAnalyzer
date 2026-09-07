from dataclasses import asdict, dataclass
from datetime import date as Date
from typing import Any

from privacy_policy_analyzer import Language, UnsupportedLanguage
from privacy_policy_analyzer.analysis import collect_information
from privacy_policy_analyzer.analysis.err import ModelLoadError
from privacy_policy_analyzer.analysis.post_processing import (
    combine_table_rows,
    propagate_headers,
    smooth_context,
)
from privacy_policy_analyzer.analysis.structure import (
    StructuredEntry,
    StructuredTextMappings,
)
from privacy_policy_analyzer.config import PipelineConfiguration
from privacy_policy_analyzer.crawl import CollectedPolicy, CrawlError, crawl
from privacy_policy_analyzer.crawl.extract_data import parse_structured_content
from privacy_policy_analyzer.crawl.language import (
    choose_fallback_language,
    detect_language_from_html,
)
from privacy_policy_analyzer.crawl.process import parse_harmonized_content
from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.shared.structure import (
    AddressOutput,
    HeaderOutput,
    LinkOutput,
    ListItemOutput,
    ListOutput,
    ParagraphOutput,
    StyledTextOutput,
    TableOutput,
    TableRowOutput,
)
from privacy_policy_analyzer.shared.util import get_device

logger = get_logger(__name__)


@dataclass
class PolicyResult:
    """
    Results of analyzing a privacy policy.
    Contains the original policy data and the analyzed structured entries.
    """

    name: str
    source: str
    language: str
    date: Date

    html: str
    structured: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableOutput
    ]
    harmonized: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableRowOutput
    ]
    text: list[str]
    analyzed: list[StructuredEntry]

    stats: dict

    @staticmethod
    def from_json(data: dict[str, Any]) -> "PolicyResult":
        name: str = data["name"]
        source: str = data["source"]
        language: Language = Language(data["language"])
        date: Date = Date.fromisoformat(data["date"])

        html: str = data["html"]

        structured_raw: list[dict] = data["structured"]
        harmonized_raw: list[dict] = data["harmonized"]
        text: list[str] = data["text"]
        analyzed_raw: list[dict] = data["analyzed"]

        structured = parse_structured_content(structured_raw)
        harmonized = parse_harmonized_content(harmonized_raw)

        analyzed = [StructuredEntry.from_dict(item) for item in analyzed_raw]

        stats = data.get("stats", {})

        return PolicyResult(
            name=name,
            source=source,
            language=language,
            date=date,
            html=html,
            structured=structured,
            harmonized=harmonized,
            text=text,
            analyzed=analyzed,
            stats=stats,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "language": self.language,
            "date": self.date.isoformat(),
            "html": self.html,
            "structured": [asdict(entry) for entry in self.structured],
            "harmonized": [asdict(entry) for entry in self.harmonized],
            "text": self.text,
            "analyzed": [asdict(entry) for entry in self.analyzed],
            "stats": self.stats,
        }


class Pipeline:
    """
    A pipeline for analyzing privacy policies.
    Combines crawling and information extraction.

    Holds one PipelineConfiguration per supported language, so the correct
    one can be selected per document - either from an explicitly given
    language, or one auto-detected from the document's content.

    Raises ModelLoadError on construction if `cache_load_models` is True and
    any configured model cannot be loaded (e.g. an invalid or unreachable
    HuggingFace repo).
    """

    configs: dict[Language, PipelineConfiguration]

    prefer_onnx: bool
    cache_load_models: bool

    allow_fallback: bool

    def __init__(
        self,
        configs: dict[Language, PipelineConfiguration],
        prefer_onnx: bool,
        cache_load_models: bool = True,
        allow_fallback: bool = True,
    ):
        """
        A pipeline for analyzing privacy policies.
        Combines crawling and information extraction.

        Holds one PipelineConfiguration per supported language, so the correct
        one can be selected per document - either from an explicitly given
        language, or one auto-detected from the document's content.

        If `prefer_onnx` is True, an ONNX version of each model is tried
        first (requires the `optimum` extra); if none is found for a given
        model, that model silently falls back to its regular PyTorch weights.

        Raises ModelLoadError on construction if `cache_load_models` is True and
        any configured model cannot be loaded (e.g. an invalid or unreachable
        HuggingFace repo).
        """
        self.configs = configs
        self.prefer_onnx = prefer_onnx
        self.cache_load_models = cache_load_models
        self.allow_fallback = allow_fallback

        logger.info("Configured languages=%s", list(configs.keys()))

        device = get_device()
        if prefer_onnx:
            device = f"CPU (ONNX Runtime) / Fallback {device}"

        logger.info("Using device: %s", device)

        if self.cache_load_models:
            logger.info("Pre-loading model loading for faster subsequent runs")
            for config in configs.values():
                logger.info(
                    "Pre-loading model loading for language=%s", config.language
                )
                config.model_configs.test_load_models(prefer_onnx)
                config.ner_model_config.test_load_models(prefer_onnx)
            logger.info("Completed pre-loading model loading for all languages")

    def run_with_policy(
        self, policy: CollectedPolicy
    ) -> PolicyResult | UnsupportedLanguage | ModelLoadError:
        """Run the pipeline with a collected policy."""

        resolved_language = policy.language
        config = self.configs.get(resolved_language)
        if config is None and self.allow_fallback:
            fallback = choose_fallback_language(self.configs.keys())
            if fallback is not None:
                logger.info("Falling back to language=%s", fallback)
                resolved_language = fallback
                config = self.configs[fallback]

        if config is None:
            logger.warning("Unsupported language=%s", policy.language)
            return UnsupportedLanguage(language=policy.language)

        mapping = StructuredTextMappings(policy.harmonized)

        logger.info("Extracting information from policy=%s", policy.name)

        error = collect_information(
            entries=mapping.raw_entries,
            model_config=config.model_configs,
            pattern_config=config.pattern_configs,
            duration_pattern_config=config.duration_pattern_configs,
            date_pattern_config=config.date_pattern_config,
            email_pattern_config=config.email_pattern_config,
            ner_model_config=config.ner_model_config,
            use_ner_for_company=config.use_ner_for_company,
            prefer_onnx=self.prefer_onnx,
            cached=self.cache_load_models,
        )
        if error is not None:
            return error
        logger.info("Completed information collection for policy=%s", policy.name)

        entries = mapping.build_structured_entries()
        propagate_stats = propagate_headers(entries)
        entries = combine_table_rows(entries)
        smoothing_stats = smooth_context(entries)

        return PolicyResult(
            name=policy.name,
            source=policy.source,
            language=resolved_language,
            date=policy.date,
            html=policy.html,
            structured=policy.structured,
            harmonized=policy.harmonized,
            text=policy.text,
            analyzed=entries,
            stats={"smoothing": smoothing_stats, "propagate": propagate_stats},
        )

    def run_with_url(
        self, name: str, url: str, preferred_language: Language | None
    ) -> PolicyResult | CrawlError | UnsupportedLanguage | ModelLoadError:
        """Run the pipeline with a URL to crawl the policy from.

        If `preferred_language` is None, it is auto-detected from the
        scraped content and the matching registered configuration is used.
        """

        logger.info(
            "Running pipeline for policy=%s preferred_language=%s",
            name,
            preferred_language,
        )

        splitter_configs = {
            lang: config.splitter_configs for lang, config in self.configs.items()
        }
        result = crawl(
            name, url, preferred_language, splitter_configs, self.allow_fallback
        )

        if isinstance(result, CrawlError | UnsupportedLanguage):
            return result

        logger.info("Completed crawl for policy=%s", result.name)
        return self.run_with_policy(result)

    def run_with_html(
        self, name: str, source: str, language: Language | None, date: Date, html: str
    ) -> PolicyResult | UnsupportedLanguage | ModelLoadError:
        """Run the pipeline with raw HTML content of a policy.

        If `language` is None, it is auto-detected from the given HTML.
        """

        logger.info(
            "Running pipeline for policy=%s language=%s",
            name,
            language,
        )

        if language is None:
            language = detect_language_from_html(html)
            logger.debug("Detected language=%s", language)

        config = self.configs.get(language)
        if config is None and self.allow_fallback:
            fallback = choose_fallback_language(self.configs.keys())
            if fallback is not None:
                logger.info("Falling back to language=%s", fallback)
                language = fallback
                config = self.configs[fallback]

        if config is None:
            logger.warning("Unsupported language=%s", language)
            return UnsupportedLanguage(language=language)

        policy = CollectedPolicy.from_parts(
            splitter_config=config.splitter_configs,
            name=name,
            source=source,
            language=language,
            date=date,
            html=html,
            structured_raw=None,
            harmonized_raw=None,
            text=None,
        )

        return self.run_with_policy(policy)
