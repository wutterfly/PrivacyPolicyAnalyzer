import math
from dataclasses import dataclass

from privacy_policy_analyzer.analysis.data_hierarchy import (
    DEFAULT_HIERARCHY,
    DataHierarchy,
)
from privacy_policy_analyzer.report.summary import SummaryReport
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)

# ---------------- Grade Boundaries ----------------


@dataclass
class GradeBoundaries:
    class_a: float  # minimum value for class A
    class_b: float  # minimum value for class B
    class_c: float  # minimum value for class C

    must_be_greater: bool  # if True, higher scores are better

    def get_grade(self, score: float) -> str:
        if self.must_be_greater:
            if score >= self.class_a:
                return "A"
            elif score >= self.class_b:
                return "B"
            elif score >= self.class_c:
                return "C"
            else:
                return "D"
        else:
            if score <= self.class_a:
                return "A"
            elif score <= self.class_b:
                return "B"
            elif score <= self.class_c:
                return "C"
            else:
                return "D"


DEFAULT_DATA_SPECIFICITY_BOUNDARIES = GradeBoundaries(
    class_a=29.71,
    class_b=25.69,
    class_c=21.54,
    must_be_greater=True,
)

DEFAULT_THIRD_PARTY_SPECIFICITY_BOUNDARIES = GradeBoundaries(
    class_a=135.00,
    class_b=92.98,
    class_c=59.46,
    must_be_greater=True,
)

DEFAULT_RETENTION_SPECIFICITY_BOUNDARIES = GradeBoundaries(
    class_a=78.62,
    class_b=49.49,
    class_c=17.63,
    must_be_greater=True,
)

# ---------------- Transparency Score ----------------


def calculate_data_specificity(
    data_types: list[str], hierarchy: DataHierarchy
) -> float:
    """Average specificity score: level^3 + (1 if leaf)"""
    if not data_types:
        return 0.0

    total_score = 0.0
    valid_count = 0

    for dt in data_types:
        result = hierarchy.find_data_type(dt)
        if result is None:
            logger.warning("Data type not found in hierarchy: data_type=%s", dt)
            continue

        score = result.level**3
        if result.is_leaf:
            score += 1

        total_score += score
        valid_count += 1

    return total_score / valid_count if valid_count > 0 else 0.0


def calculate_third_party_specificity(
    summary: SummaryReport,
) -> float | None:
    third_party_sentences = summary.third_party.third_party_sentences

    third_party_sentences = max(
        0,
        third_party_sentences
        - summary.third_party.official
        - summary.third_party.same_company
        - summary.third_party.public,
    )

    if third_party_sentences == 0:
        return None

    descriptive = summary.third_party.descriptive + summary.third_party.company * 2

    return (descriptive / third_party_sentences) * 100


def calculate_retention_specificity(
    summary: SummaryReport,
) -> float:
    DURATION_WEIGHT = 5
    LEGAL_BASIS_WEIGHT = 3
    STATUTORY_WEIGHT = 2
    NECESSITY_WEIGHT = 1

    duration = summary.retention.duration
    legal_basis = summary.retention.legal_basis
    statutory = summary.retention.statutory
    necessity = summary.retention.necessity

    if duration + legal_basis + statutory + necessity == 0:
        return 0.0

    total = (
        (duration * DURATION_WEIGHT)
        + (legal_basis * LEGAL_BASIS_WEIGHT)
        + (statutory * STATUTORY_WEIGHT)
        + (necessity * NECESSITY_WEIGHT)
    )

    normalized = min(100, (math.log1p(total) / math.log1p(50)) * 100)

    return float(normalized)


@dataclass
class TransparencyScore:
    data_specificity: float
    data_specificity_grade: str

    third_party_specificity: float | None
    third_party_specificity_grade: str | None

    calculate_retention_specificity: float
    retention_specificity_grade: str


def calculate_transparency(
    summary: SummaryReport,
    hierarchy: DataHierarchy,
    data_boundaries: GradeBoundaries,
    third_party_boundaries: GradeBoundaries,
    data_retention_boundaries: GradeBoundaries,
) -> TransparencyScore:
    # Data Specificity
    data_specificity = calculate_data_specificity(
        summary.data_type.data_types, hierarchy
    )
    data_grade = data_boundaries.get_grade(data_specificity)

    # Third-Party Specificity
    third_party_specificity = calculate_third_party_specificity(summary)
    third_party_grade = (
        third_party_boundaries.get_grade(third_party_specificity)
        if third_party_specificity is not None
        else None
    )

    # Retention Specificity
    retention_specificity = calculate_retention_specificity(summary)
    retention_grade = data_retention_boundaries.get_grade(retention_specificity)

    return TransparencyScore(
        data_specificity=data_specificity,
        data_specificity_grade=data_grade,
        third_party_specificity=third_party_specificity,
        third_party_specificity_grade=third_party_grade,
        calculate_retention_specificity=retention_specificity,
        retention_specificity_grade=retention_grade,
    )


# ---------------- Coverage Score ----------------

COVERAGE_MAX_SCORE: int = 17


@dataclass
class CoverageScore:
    sec_transmission: bool
    sec_physical: bool
    sec_organizational: bool
    sec_technical: bool
    sec_contract: bool
    children_mentioned: bool
    third_party_official: bool
    selling_merge: bool

    user_right_access: bool
    user_right_rectification: bool
    user_right_deletion: bool
    user_right_restriction: bool
    user_right_withdrawal: bool
    user_right_data_portability: bool
    user_right_object: bool
    user_right_complaint: bool
    user_right_no_discrimination: bool | None

    final_score: float


def calculate_coverage_score(summary: SummaryReport) -> CoverageScore:
    # Security & Privacy
    sec_transmission = summary.security_privacy.transmission
    sec_physical = summary.security_privacy.physical
    sec_organizational = summary.security_privacy.organizational
    sec_technical = summary.security_privacy.technical > 0
    sec_contract = summary.security_privacy.contractual > 0

    # Children Mentioned
    children_mentioned = summary.audience.children

    # Third Party Official
    third_party_official = summary.third_party.official > 0

    # Merger
    selling_merger = summary.selling.merger_acquisition

    # User Rights
    user_right_access = summary.user_rights.access
    user_right_deletion = summary.user_rights.deletion
    user_right_rectification = summary.user_rights.rectification
    user_right_restriction = summary.user_rights.restriction
    user_right_revoke = summary.user_rights.revoke
    user_right_data_portability = summary.user_rights.data_portability
    user_right_object = summary.user_rights.object
    user_right_complaint = summary.user_rights.complain
    user_right_no_discrimination = summary.user_rights.no_discrimination

    # Adjust max score if no_discrimination is None
    max_score = (
        COVERAGE_MAX_SCORE - 1
        if user_right_no_discrimination is None
        else COVERAGE_MAX_SCORE
    )

    total = [
        sec_transmission,
        sec_physical,
        sec_organizational,
        sec_technical,
        sec_contract,
        children_mentioned,
        third_party_official,
        selling_merger,
        user_right_access,
        user_right_deletion,
        user_right_restriction,
        user_right_rectification,
        user_right_revoke,
        user_right_data_portability,
        user_right_object,
        user_right_complaint,
        user_right_no_discrimination,
    ].count(True)

    final_score = (total / max_score) * 100

    return CoverageScore(
        sec_transmission=sec_transmission,
        sec_physical=sec_physical,
        sec_organizational=sec_organizational,
        sec_technical=sec_technical,
        sec_contract=sec_contract,
        children_mentioned=children_mentioned,
        third_party_official=third_party_official,
        selling_merge=selling_merger,
        user_right_access=user_right_access,
        user_right_deletion=user_right_deletion,
        user_right_restriction=user_right_restriction,
        user_right_rectification=user_right_rectification,
        user_right_withdrawal=user_right_revoke,
        user_right_data_portability=user_right_data_portability,
        user_right_object=user_right_object,
        user_right_complaint=user_right_complaint,
        user_right_no_discrimination=user_right_no_discrimination,
        final_score=final_score,
    )


# ---------------- Meta Score ----------------

META_MAX_SCORE: int = 6


@dataclass
class MetaScore:
    contact_phone: bool
    contact_email: bool
    contact_address: bool
    contact_website: bool

    policy_date: bool
    policy_officer: bool

    final_score: float


def calculate_meta_score(summary: SummaryReport) -> MetaScore:
    # Contact aspects
    phone = summary.contact.phone
    email = summary.contact.email
    address = summary.contact.address
    website = summary.contact.website

    # Policy aspects
    date = summary.policy.date is not None
    officer = summary.policy.data_protection_officer

    total = [
        phone,
        email,
        address,
        website,
        date,
        officer,
    ].count(True)

    return MetaScore(
        contact_phone=phone,
        contact_email=email,
        contact_address=address,
        contact_website=website,
        policy_date=date,
        policy_officer=officer,
        final_score=(total / META_MAX_SCORE) * 100,
    )


# ---------------- Score Report ----------------


@dataclass
class ScoreReport:
    transparency: TransparencyScore
    coverage: CoverageScore
    meta: MetaScore

    @staticmethod
    def from_json(data: dict) -> "ScoreReport":
        return ScoreReport(
            transparency=TransparencyScore(**data["transparency"]),
            coverage=CoverageScore(**data["coverage"]),
            meta=MetaScore(**data["meta"]),
        )


def create_score_report(
    summary: SummaryReport,
    hierarchy: DataHierarchy = DEFAULT_HIERARCHY,
    data_grading: GradeBoundaries = DEFAULT_DATA_SPECIFICITY_BOUNDARIES,
    third_party_grading: GradeBoundaries = DEFAULT_THIRD_PARTY_SPECIFICITY_BOUNDARIES,
    data_retention_grading: GradeBoundaries = DEFAULT_RETENTION_SPECIFICITY_BOUNDARIES,
) -> ScoreReport:
    data = calculate_transparency(
        summary, hierarchy, data_grading, third_party_grading, data_retention_grading
    )
    coverage = calculate_coverage_score(summary)
    meta = calculate_meta_score(summary)

    return ScoreReport(transparency=data, coverage=coverage, meta=meta)
