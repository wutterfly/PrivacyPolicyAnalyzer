from dataclasses import asdict, dataclass
from datetime import date as Date
from typing import Any

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.analysis import collect_information
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
class MismatchedLanguages:
    pipeline: Language
    policy: Language


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
    """

    config: PipelineConfiguration

    onnx: bool
    cache_load_models: bool

    def __init__(
        self,
        config: PipelineConfiguration,
        onnx: bool,
        cache_load_models: bool = True,
    ):
        self.config = config
        self.onnx = onnx
        self.cache_load_models = cache_load_models

        if onnx:
            logger.info("Using device: %s", "CPU (ONNX)")
        else:
            logger.info("Using device: %s", get_device())

        if cache_load_models:
            config.model_configs.test_load_models(onnx)
            config.ner_model_config.test_load_models(onnx)

    @property
    def language(self) -> Language:
        return self.config.language

    def run_with_policy(
        self, policy: CollectedPolicy
    ) -> PolicyResult | MismatchedLanguages:
        """Run the pipeline with a collected policy."""

        if self.config.language != policy.language:
            return MismatchedLanguages(
                pipeline=self.config.language, policy=policy.language
            )

        mapping = StructuredTextMappings(policy.harmonized)

        logger.debug(
            "Collecting information for policy=%s source=%s", policy.name, policy.source
        )

        collect_information(
            entries=mapping.raw_entries,
            model_config=self.config.model_configs,
            pattern_config=self.config.pattern_configs,
            duration_pattern_config=self.config.duration_pattern_configs,
            date_pattern_config=self.config.date_pattern_config,
            email_pattern_config=self.config.email_pattern_config,
            ner_model_config=self.config.ner_model_config,
            use_ner_for_company=self.config.use_ner_for_company,
            onnx=self.onnx,
            cached=self.cache_load_models,
        )
        logger.debug("Completed information collection for policy=%s", policy.name)

        entries = mapping.build_structured_entries()
        propagate_stats = propagate_headers(entries)
        entries = combine_table_rows(entries)
        smoothing_stats = smooth_context(entries)

        return PolicyResult(
            name=policy.name,
            source=policy.source,
            language=policy.language,
            date=policy.date,
            html=policy.html,
            structured=policy.structured,
            harmonized=policy.harmonized,
            text=policy.text,
            analyzed=entries,
            stats={"smoothing": smoothing_stats, "propagate": propagate_stats},
        )

    def run_with_url(
        self, name: str, url: str, language: Language
    ) -> PolicyResult | CrawlError:
        """Run the pipeline with a URL to crawl the policy from."""

        result = crawl(name, url, language, self.config.splitter_configs)

        if isinstance(result, CrawlError):
            return result

        output = self.run_with_policy(result)
        assert isinstance(output, PolicyResult)
        return output

    def run_with_html(
        self, name: str, source: str, language: Language, date: Date, html: str
    ) -> PolicyResult:
        """Run the pipeline with raw HTML content of a policy."""

        policy = CollectedPolicy.from_parts(
            splitter_config=self.config.splitter_configs,
            name=name,
            source=source,
            language=language,
            date=date,
            html=html,
            structured_raw=None,
            harmonized_raw=None,
            text=None,
        )

        output = self.run_with_policy(policy)
        assert isinstance(output, PolicyResult)
        return output
