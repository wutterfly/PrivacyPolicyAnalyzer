from dataclasses import asdict, dataclass
from datetime import date

from privacy_policy_analyzer.analysis.data_hierarchy import (
    DEFAULT_HIERARCHY,
    DataHierarchy,
)
from privacy_policy_analyzer.analysis.structure import StructuredEntry
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)

# -------------- Definition Entry -----------------


def is_definition_entry(entry: StructuredEntry) -> bool:
    for tpc in entry.topics:
        if tpc.topic == "Policy":
            for cnt in tpc.contents:
                if cnt.content == "Definition":
                    return True
    return False


# --------------- Security/Privacy -----------------


@dataclass
class SecurityPrivacyInformation:
    transmission: bool
    physical: bool
    organizational: bool
    hints: int

    technical: int
    contractual: int

    technical_privacy: list[str]
    technical_security: list[str]
    contractuals: list[str]

    @staticmethod
    def from_json(data: dict) -> "SecurityPrivacyInformation":
        return SecurityPrivacyInformation(
            transmission=bool(data["transmission"]),
            physical=bool(data["physical"]),
            organizational=bool(data["organizational"]),
            hints=int(data["hints"]),
            technical=int(data["technical"]),
            contractual=int(data["contractual"]),
            technical_privacy=list(data["technical_privacy"]),
            technical_security=list(data["technical_security"]),
            contractuals=list(data["contractuals"]),
        )


def extract_security_privacy_information(
    data: list[StructuredEntry],
) -> SecurityPrivacyInformation:
    transmission = False
    physical = False
    organizational = False
    hints = 0

    technical = 0
    contractual = 0

    technical_privacy = set()
    technical_security = set()
    contractuals = set()

    for entry in data:
        for tpc in entry.topics:
            if tpc.topic != "Security/Privacy":
                continue

            for cnt in tpc.contents:
                if cnt.content == "TransmissionSecurity":
                    transmission = True
                elif cnt.content == "PhysicalSecurityMeasures":
                    physical = True
                elif cnt.content == "OrganisationalSecurityMeasures":
                    organizational = True
                elif cnt.content == "TechnicalPrivacyMeasures":
                    technical += 1
                    technical_privacy.update(cnt.attributes)
                elif cnt.content == "TechnicalSecurityMeasures":
                    technical += 1
                    technical_security.update(cnt.attributes)
                elif cnt.content == "ContractualSecurityMeasures":
                    contractual += 1
                    contractuals.update(cnt.attributes)
                elif cnt.content == "SecurityHints":
                    hints += 1

    #
    return SecurityPrivacyInformation(
        transmission=transmission,
        physical=physical,
        organizational=organizational,
        hints=hints,
        technical=technical,
        contractual=contractual,
        technical_privacy=list(technical_privacy),
        technical_security=list(technical_security),
        contractuals=list(contractuals),
    )


# --------------- Legal Basis -----------------


@dataclass
class LegalBasisInformation:
    total: int
    consent: int
    contract: int
    legal_obligation: int
    public_interest: int
    vital_interests: int
    legitimate_interest: int
    employment: int

    @staticmethod
    def from_json(data: dict) -> "LegalBasisInformation":
        return LegalBasisInformation(
            total=int(data["total"]),
            consent=int(data["consent"]),
            contract=int(data["contract"]),
            legal_obligation=int(data["legal_obligation"]),
            public_interest=int(data["public_interest"]),
            vital_interests=int(data["vital_interests"]),
            legitimate_interest=int(data["legitimate_interest"]),
            employment=int(data["employment"]),
        )


def extract_legal_basis_information(
    data: list[StructuredEntry],
) -> LegalBasisInformation:
    consent = 0
    contract = 0
    legal_obligation = 0
    public_interest = 0
    vital_interests = 0
    legitimate_interest = 0
    employment = 0

    for entry in data:
        for tpc in entry.topics:
            if tpc.topic != "LegalBasis":
                continue

            for cnt in tpc.contents:
                if cnt.content == "Consent":
                    consent += 1
                elif cnt.content == "Contract":
                    contract += 1
                elif cnt.content == "LegalObligation":
                    legal_obligation += 1
                elif cnt.content == "PublicInterests":
                    public_interest += 1
                elif cnt.content == "VitalInterests":
                    vital_interests += 1
                elif cnt.content == "LegitimateInterests":
                    legitimate_interest += 1
                elif cnt.content == "EmploymentProcedure":
                    employment += 1

    return LegalBasisInformation(
        total=consent
        + contract
        + legal_obligation
        + public_interest
        + vital_interests
        + legitimate_interest
        + employment,
        consent=consent,
        contract=contract,
        legal_obligation=legal_obligation,
        public_interest=public_interest,
        vital_interests=vital_interests,
        legitimate_interest=legitimate_interest,
        employment=employment,
    )


# --------------- User Rights -----------------


@dataclass
class UserRightsInformation:
    access: bool
    rectification: bool
    deletion: bool
    restriction: bool
    data_portability: bool
    object: bool
    revoke: bool
    complain: bool
    no_discrimination: None | bool

    @staticmethod
    def from_json(data: dict) -> "UserRightsInformation":
        return UserRightsInformation(
            access=bool(data["access"]),
            rectification=bool(data["rectification"]),
            deletion=bool(data["deletion"]),
            restriction=bool(data["restriction"]),
            data_portability=bool(data["data_portability"]),
            object=bool(data["object"]),
            revoke=bool(data["revoke"]),
            complain=bool(data["complain"]),
            no_discrimination=data["no_discrimination"],
        )


def extract_user_rights_information(
    data: list[StructuredEntry],
) -> UserRightsInformation:
    access = False
    rectification = False
    deletion = False
    restriction = False
    data_portability = False
    objection = False
    revoke = False
    complain = False
    no_discrimination = False

    california_specific = False

    for entry in data:
        for tpc in entry.topics:
            if tpc.topic not in ["UserRights"]:
                continue

            if tpc.topic == "Audience":
                for cnt in tpc.contents:
                    if cnt.content == "Country":
                        if "California" in cnt.attributes:
                            california_specific = True

                continue

            for cnt in tpc.contents:
                if cnt.content == "DataAccess":
                    access = True
                elif cnt.content == "RevokeConsent":
                    revoke = True
                elif cnt.content == "DataRectification":
                    rectification = True
                elif cnt.content == "DataErasure":
                    deletion = True
                elif cnt.content == "RestrictProcessing":
                    restriction = True
                elif cnt.content == "DataPortability":
                    data_portability = True
                elif cnt.content == "Object":
                    objection = True
                elif cnt.content == "Complain":
                    complain = True
                elif cnt.content == "NotBeDiscriminated":
                    no_discrimination = True

    # adjust no_discrimination based on california specificity
    if not california_specific and not no_discrimination:
        no_discrimination = None

    return UserRightsInformation(
        access=access,
        rectification=rectification,
        deletion=deletion,
        restriction=restriction,
        data_portability=data_portability,
        object=objection,
        revoke=revoke,
        complain=complain,
        no_discrimination=no_discrimination,
    )


# --------------- Audience -----------------


@dataclass
class AudienceInformation:
    children: bool  # whether children are addressed
    children_processing: bool  # whether children data is processed

    beta_tester: bool

    audience_countries: list[str]

    @staticmethod
    def from_json(data: dict) -> "AudienceInformation":
        return AudienceInformation(
            children=bool(data["children"]),
            children_processing=bool(data["children_processing"]),
            audience_countries=list(data["audience_countries"]),
            beta_tester=bool(data["beta_tester"]),
        )


def extract_audience_information(data: list[StructuredEntry]) -> AudienceInformation:
    children = False
    children_processing = False

    # check for children and not processing
    for entry in data:
        _children = False
        _not_processing = False
        for tpc in entry.topics:
            if tpc.topic != "Audience":
                continue

            for cnt in tpc.contents:
                if cnt.content == "Children":
                    _children = True
                    children = True
                    children_processing = True
                    break

        for tpc in entry.topics:
            if tpc.topic != "Processing":
                continue

            for cnt in tpc.contents:
                if cnt.content == "NotProcessing":
                    _not_processing = True
                    break

        if _children and _not_processing:
            children_processing = False
            break

    # check for country specific audience
    audience_countries = set()
    for entry in data:
        for tpc in entry.topics:
            if tpc.topic != "Audience":
                continue

            for cnt in tpc.contents:
                if cnt.content == "Country":
                    audience_countries.update(cnt.attributes)

    audience_countries.discard("ResidenceState")
    audience_countries.discard("CountriesOutsideOf")
    audience_countries.discard("AndOther")

    # check for beta tester audience
    beta_tester = False
    for entry in data:
        for tpc in entry.topics:
            if tpc.topic != "Audience":
                continue

            for cnt in tpc.contents:
                if cnt.content == "BetaTester":
                    beta_tester = True

    return AudienceInformation(
        children=children,
        children_processing=children_processing,
        audience_countries=list(audience_countries),
        beta_tester=beta_tester,
    )


#  --------------- Purpose Information -----------------


@dataclass
class PurposeInformation:
    improve: int
    provide: int
    security: int
    compliance: int
    customer_acq: int
    communication: int
    operational: int
    significant: int
    analytics: int

    purposes: list[str]
    third_party_purposes: list[str]

    @staticmethod
    def from_json(data: dict) -> "PurposeInformation":
        return PurposeInformation(
            improve=int(data["improve"]),
            provide=int(data["provide"]),
            security=int(data["security"]),
            compliance=int(data["compliance"]),
            customer_acq=int(data["customer_acq"]),
            communication=int(data["communication"]),
            operational=int(data["operational"]),
            significant=int(data["significant"]),
            analytics=int(data["analytics"]),
            purposes=list(data["purposes"]),
            third_party_purposes=list(data["third_party_purposes"]),
        )


def extract_purpose_information(data: list[StructuredEntry]) -> PurposeInformation:
    improve = 0
    provide = 0
    security = 0
    compliance = 0
    customer_acq = 0
    communication = 0
    operational = 0
    significant = 0
    analytics = 0

    purposes = set()
    third_party_purposes = set()

    for entry in data:
        # check whether processing, sharing, retention, or selling is not done
        skip = False
        for tpc in entry.topics:
            if skip:
                break

            if tpc.topic == "Processing":
                for cnt in tpc.contents:
                    if cnt.content == "NotProcessing":
                        skip = True
                        break
                    elif cnt.content == "Profiling":
                        for attr in cnt.attributes:
                            if attr == "NotProfiling":
                                skip = True
                                break

            if tpc.topic == "Sharing":
                for cnt in tpc.contents:
                    if cnt.content == "NotSharing":
                        skip = True
                        break

            if tpc.topic == "Retention":
                for cnt in tpc.contents:
                    if cnt.content == "NotRetention":
                        skip = True
                        break

            if tpc.topic == "Selling":
                for cnt in tpc.contents:
                    if cnt.content == "NotSelling":
                        skip = True
                        break

        # if it's negated, skip
        if skip:
            continue

        for tpc in entry.topics:
            if tpc.topic != "Purpose":
                continue

            is_third_party = False
            for tpc_t in entry.topics:
                if tpc_t.topic == "ThirdParty":
                    is_third_party = True
                    break

            items = set()

            for cnt in tpc.contents:
                if cnt.content == "ImproveService":
                    improve += 1
                    items.add("ImproveService")
                elif cnt.content == "ProvideService":
                    provide += 1
                    items.update(
                        cnt.attributes if cnt.attributes else ["ProvideService"]
                    )
                elif cnt.content == "Security":
                    security += 1
                    items.add("Security")
                elif cnt.content == "Compliance":
                    compliance += 1
                    items.add("Compliance")
                elif cnt.content == "CustomerAcquisition":
                    customer_acq += 1
                    items.add("CustomerAcquisition")
                elif cnt.content == "Communication":
                    communication += 1
                    items.update(
                        cnt.attributes if cnt.attributes else ["Communication"]
                    )
                elif cnt.content == "Operational":
                    operational += 1
                    items.add("Operational")
                elif cnt.content == "SignificantEffects":
                    significant += 1
                    items.add("SignificantEffects")
                elif cnt.content == "Analytics":
                    analytics += 1
                    items.add("Analytics")

            if is_third_party:
                third_party_purposes.update(items)
            else:
                purposes.update(items)

    return PurposeInformation(
        improve=improve,
        provide=provide,
        security=security,
        compliance=compliance,
        customer_acq=customer_acq,
        communication=communication,
        operational=operational,
        significant=significant,
        analytics=analytics,
        purposes=list(purposes),
        third_party_purposes=list(third_party_purposes),
    )


# --------------- Third Party -----------------


@dataclass
class ThirdPartyInformation:
    third_party_sentences: int

    official: int
    same_company: int
    public: int
    descriptive: int
    company: int

    descriptives: list[str]
    companies: list[str]

    @staticmethod
    def from_json(data: dict) -> "ThirdPartyInformation":
        return ThirdPartyInformation(
            third_party_sentences=int(data["third_party_sentences"]),
            official=int(data["official"]),
            same_company=int(data["same_company"]),
            public=int(data["public"]),
            descriptive=int(data["descriptive"]),
            company=int(data["company"]),
            descriptives=list(data["descriptives"]),
            companies=list(data["companies"]),
        )


def extract_third_party_information(
    data: list[StructuredEntry],
) -> ThirdPartyInformation:
    third_party_sentences = 0

    official = 0
    same_company = 0
    public = 0
    descriptive = 0
    company = 0

    descriptives = set()
    companies = set()

    for entry in data:
        for tpc in entry.topics:
            if tpc.topic != "ThirdParty":
                continue

            third_party_sentences += 1

            for cnt in tpc.contents:
                if cnt.content == "Descriptive":
                    descriptive += 1
                    descriptives.update(cnt.attributes)
                elif cnt.content == "Company":
                    company += 1
                    companies.update(cnt.attributes)
                elif cnt.content == "Official":
                    official += 1
                elif cnt.content == "SameCompany":
                    same_company += 1
                elif cnt.content == "Public":
                    public += 1

    return ThirdPartyInformation(
        third_party_sentences=third_party_sentences,
        official=official,
        same_company=same_company,
        public=public,
        descriptive=descriptive,
        company=company,
        descriptives=list(descriptives),
        companies=list(companies),
    )


# --------------- Data Type -----------------


@dataclass
class DataTypeInformation:
    data_types: list[str]
    data_types_level: dict[int, list[str]]

    beta_tester_data_types: list[str]
    beta_tester_data_types_level: dict[int, list[str]]

    @staticmethod
    def from_json(data: dict) -> "DataTypeInformation":
        return DataTypeInformation(
            data_types=list(data["data_types"]),
            data_types_level={
                int(k): list(v) for k, v in data["data_types_level"].items()
            },
            beta_tester_data_types=list(data["beta_tester_data_types"]),
            beta_tester_data_types_level={
                int(k): list(v) for k, v in data["beta_tester_data_types_level"].items()
            },
        )


def collect_data_types_by_level(
    data_types: set[str],
    hierarchy: DataHierarchy,
) -> dict[int, list[str]]:
    data_type_count: dict[int, set[str]] = {}

    for data_type in data_types:
        hierarchy_entry = hierarchy.find_data_type(data_type)
        if hierarchy_entry is None:
            logger.warning("Data type not found in hierarchy: data_type=%s", data_type)
            continue

        for level, dt in enumerate(hierarchy_entry.path):
            if level == 0:
                continue  # skip root

            if level not in data_type_count:
                data_type_count[level] = set()
            data_type_count[level].add(dt)

    return {level: list(dts) for level, dts in data_type_count.items()}


def extract_data_type_information(
    data: list[StructuredEntry],
    hierarchy: DataHierarchy,
) -> DataTypeInformation:
    data_types = set()
    beta_tester_data_types = set()

    # extract data types
    look_in = ["Processing", "Sharing", "Retention", "Deletion", "Selling"]
    for entry in data:
        beta_tester = False
        for tpc in entry.topics:
            if tpc.topic == "Audience":
                for cnt in tpc.contents:
                    if cnt.content == "BetaTester":
                        beta_tester = True
                        break

        for tpc in entry.topics:
            # check only relevant topics
            if tpc.topic in look_in:
                for cnt in tpc.contents:
                    if cnt.content == "DataType":
                        if beta_tester:
                            beta_tester_data_types.update(cnt.attributes)
                        else:
                            data_types.update(cnt.attributes)
                        break

    data_types_level = collect_data_types_by_level(data_types, hierarchy)
    beta_tester_data_types_level = collect_data_types_by_level(
        beta_tester_data_types, hierarchy
    )

    return DataTypeInformation(
        data_types=list(data_types),
        data_types_level=data_types_level,
        beta_tester_data_types=list(beta_tester_data_types),
        beta_tester_data_types_level=beta_tester_data_types_level,
    )


# --------------- Processing Information -----------------


@dataclass
class ProcessingInformation:
    profiling: bool | None
    automated_decision: bool | None

    tracking: list[str]
    method_source: list[str]

    @staticmethod
    def from_json(data: dict) -> "ProcessingInformation":
        return ProcessingInformation(
            profiling=data["profiling"],
            automated_decision=data["automated_decision"],
            tracking=list(data["tracking"]),
            method_source=list(data["method_source"]),
        )


def extract_processing_information(
    data: list[StructuredEntry],
) -> ProcessingInformation:
    profiling = None
    automated_decision = None

    tracking = set()
    method_source = set()

    for entry in data:
        if is_definition_entry(entry):
            continue

        for tpc in entry.topics:
            if tpc.topic != "Processing":
                continue

            for cnt in tpc.contents:
                if cnt.content == "Profiling":
                    _not = "NotProfiling" in cnt.attributes

                    # if profiling is not already true, set it to false
                    if profiling is None:
                        profiling = not _not
                    elif profiling is False:
                        if not _not:
                            profiling = True

                elif cnt.content == "AutomatedDecisionMaking":
                    _not = "NotAutomatedDecisionMaking" in cnt.attributes

                    # if automated decision is not already true, set it to false
                    if automated_decision is None:
                        automated_decision = not _not
                    elif automated_decision is False:
                        if not _not:
                            automated_decision = True

                elif cnt.content == "Tracking/Conversion":
                    tracking.update(cnt.attributes)
                elif cnt.content == "Method/Source":
                    method_source.update(cnt.attributes)

    return ProcessingInformation(
        profiling=profiling,
        automated_decision=automated_decision,
        tracking=list(tracking),
        method_source=list(method_source),
    )


# --------------- Sharing Information -----------------


@dataclass
class SharingInformation:
    sharing_types: list[str]

    @staticmethod
    def from_json(data: dict) -> "SharingInformation":
        return SharingInformation(
            sharing_types=list(data["sharing_types"]),
        )


def extract_sharing_information(
    data: list[StructuredEntry],
) -> SharingInformation:
    sharing_types = set()

    for entry in data:
        if is_definition_entry(entry):
            continue

        for tpc in entry.topics:
            if tpc.topic != "Sharing":
                continue

            skip = False
            for cnt in tpc.contents:
                if cnt.content == "NotSharing":
                    skip = True
                    break
            if skip:
                continue

            for cnt in tpc.contents:
                if cnt.content == "DataType":
                    sharing_types.update(cnt.attributes)
                    break

    return SharingInformation(
        sharing_types=list(sharing_types),
    )


# --------------- Selling Information -----------------


@dataclass
class SellingInformation:
    data_types: list[str]

    merger_acquisition: bool
    selling_not_merger_acquisition: bool

    @staticmethod
    def from_json(data: dict) -> "SellingInformation":
        return SellingInformation(
            data_types=list(data["data_types"]),
            merger_acquisition=bool(data["merger_acquisition"]),
            selling_not_merger_acquisition=bool(data["selling_not_merger_acquisition"]),
        )


def extract_selling_information(
    data: list[StructuredEntry],
) -> SellingInformation:
    data_types = set()
    merger_acquisition = False
    selling_not_merger_acquisition = False

    for entry in data:
        if is_definition_entry(entry):
            continue

        selling = False
        is_merger_acquisition = False
        is_not_selling = False
        items = set()

        # extract selling information
        for tpc in entry.topics:
            if tpc.topic != "Selling":
                continue

            selling = True

            for cnt in tpc.contents:
                if cnt.content == "NotSelling":
                    is_not_selling = True
                elif cnt.content == "Merger/Acquisition":
                    is_merger_acquisition = True
                elif cnt.content == "DataType":
                    items.update(cnt.attributes)

        # skip if not selling is done
        if not selling or is_not_selling:
            continue

        # classify selling type
        if is_merger_acquisition:
            merger_acquisition = True
        else:
            selling_not_merger_acquisition = True

        data_types.update(items)

    return SellingInformation(
        data_types=list(data_types),
        merger_acquisition=merger_acquisition,
        selling_not_merger_acquisition=selling_not_merger_acquisition,
    )


# --------------- Retention Information -----------------


@dataclass
class RetentionInformation:
    duration: int
    statutory: int
    legal_basis: int
    necessity: int

    countries: list[str]

    @staticmethod
    def from_json(data: dict) -> "RetentionInformation":
        return RetentionInformation(
            duration=int(data["duration"]),
            statutory=int(data["statutory"]),
            legal_basis=int(data["legal_basis"]),
            necessity=int(data["necessity"]),
            countries=list(data["countries"]),
        )


def extract_retention_information(
    data: list[StructuredEntry],
) -> RetentionInformation:
    duration = 0
    statutory = 0
    legal_basis = 0
    necessity = 0

    countries = set()

    for entry in data:
        if is_definition_entry(entry):
            continue

        for tpc in entry.topics:
            if tpc.topic != "Retention":
                continue

            for cnt in tpc.contents:
                if cnt.content == "NotRetention":
                    continue

                if cnt.content == "StorageDuration":
                    duration += 1
                elif cnt.content == "StatutoryRetention":
                    statutory += 1
                elif cnt.content == "LegalBasisDuration":
                    legal_basis += 1
                elif cnt.content == "Necessity":
                    necessity += 1
                elif cnt.content == "Country":
                    countries.update(cnt.attributes)

    return RetentionInformation(
        duration=duration,
        statutory=statutory,
        legal_basis=legal_basis,
        necessity=necessity,
        countries=list(countries),
    )


# --------------- Change Information -----------------


@dataclass
class PolicyInformation:
    total_sentences: int
    date: str | None
    external_ref: int

    data_protection_officer: bool

    @staticmethod
    def from_json(data: dict) -> "PolicyInformation":
        return PolicyInformation(
            total_sentences=int(data["total_sentences"]),
            date=data["date"],
            external_ref=int(data["external_ref"]),
            data_protection_officer=bool(data["data_protection_officer"]),
        )


def extract_change_information(
    data: list[StructuredEntry],
) -> PolicyInformation:
    highest_date: date | None = None
    external_ref = 0

    data_protection_officer = False

    for entry in data:
        for tpc in entry.topics:
            if tpc.topic != "Policy":
                continue

            # extract change
            for cnt in tpc.contents:
                if cnt.content != "Change":
                    continue

                for attr in cnt.attributes:
                    try:
                        found = date.strptime(attr, "%Y-%m-%d")

                        if highest_date is None or found > highest_date:
                            highest_date = found

                    except Exception:
                        continue

            # extract external reference
            for cnt in tpc.contents:
                if cnt.content == "External":
                    external_ref += 1
                elif cnt.content == "DataProtectionOfficer":
                    data_protection_officer = True

    return PolicyInformation(
        date=highest_date.isoformat() if highest_date is not None else None,
        total_sentences=len(data),
        external_ref=external_ref,
        data_protection_officer=data_protection_officer,
    )


# --------------- Context Information -----------------


@dataclass
class ContextInformation:
    website: int
    app: int
    device: int
    store: int
    backend: int
    recruitment: int
    communication: int
    account: int
    services: int
    event: int
    other: int

    @staticmethod
    def from_json(data: dict) -> "ContextInformation":
        return ContextInformation(
            website=int(data["website"]),
            app=int(data["app"]),
            device=int(data["device"]),
            store=int(data["store"]),
            backend=int(data["backend"]),
            recruitment=int(data["recruitment"]),
            communication=int(data["communication"]),
            account=int(data["account"]),
            services=int(data["services"]),
            event=int(data["event"]),
            other=int(data["other"]),
        )


def extract_context_information(
    data: list[StructuredEntry],
) -> ContextInformation:
    website = 0
    app = 0
    device = 0
    store = 0
    backend = 0
    recruitment = 0
    communication = 0
    account = 0
    services = 0
    event = 0
    other = 0

    for entry in data:
        for ctx in entry.contexts:
            if ctx == "Website":
                website += 1
            elif ctx == "App":
                app += 1
            elif ctx == "Device":
                device += 1
            elif ctx == "Store":
                store += 1
            elif ctx == "BackendService":
                backend += 1
            elif ctx == "Recruitment":
                recruitment += 1
            elif ctx == "Communication":
                communication += 1
            elif ctx == "Account":
                account += 1
            elif ctx == "Services":
                services += 1
            elif ctx == "Event/Program":
                event += 1
            elif ctx == "Other":
                other += 1
            else:
                assert False

    return ContextInformation(
        website=website,
        app=app,
        device=device,
        store=store,
        backend=backend,
        recruitment=recruitment,
        communication=communication,
        account=account,
        services=services,
        event=event,
        other=other,
    )


# --------------- Contact Information -----------------


@dataclass
class ContactInformation:
    email: bool
    phone: bool
    website: bool
    address: bool

    email_addresses: list[str]
    phone_numbers: list[str]

    @staticmethod
    def from_json(data: dict) -> "ContactInformation":
        return ContactInformation(
            email=bool(data["email"]),
            phone=bool(data["phone"]),
            website=bool(data["website"]),
            address=bool(data["address"]),
            email_addresses=list(data.get("email_addresses", [])),
            phone_numbers=list(data.get("phone_numbers", [])),
        )


def extract_contact_information(data: list[StructuredEntry]) -> ContactInformation:
    mail = False
    phone = False
    website = False
    address = False
    emails = []
    phone_numbers = []

    for entry in data:
        # skip references to external policy
        is_external = False
        for tpc in entry.topics:
            if tpc.topic == "Policy":
                for cnt in tpc.contents:
                    if cnt.content == "External":
                        is_external = True
                        break
        if is_external:
            continue

        for tpc in entry.topics:
            if tpc.topic != "Contact":
                continue

            for cnt in tpc.contents:
                if cnt.content == "Email":
                    mail = True
                    for attr in cnt.attributes:
                        if "@" in attr:
                            emails.append(attr)
                    emails = list(set(emails))

                elif cnt.content == "Phone":
                    phone = True
                elif cnt.content == "Website":
                    website = True
                elif cnt.content == "Address":
                    address = True

    return ContactInformation(
        email=mail,
        phone=phone,
        website=website,
        address=address,
        email_addresses=emails,
        phone_numbers=phone_numbers,
    )


# --------------- Boilerplate Information -----------------


@dataclass
class BoilerplateInformation:
    boilerplate_sentences: int
    boilerplate_sentences_percentage: float

    @staticmethod
    def from_json(data: dict) -> "BoilerplateInformation":
        return BoilerplateInformation(
            boilerplate_sentences=int(data["boilerplate_sentences"]),
            boilerplate_sentences_percentage=float(
                data["boilerplate_sentences_percentage"]
            ),
        )


def extract_boilerplate_information(
    data: list[StructuredEntry],
) -> BoilerplateInformation:
    boilerplate_sentences = 0

    for entry in data:
        # only consider sentences that have 1 topic
        if len(entry.topics) > 1:
            continue

        # check that the only topic is "Other"
        for tpc in entry.topics:
            if tpc.topic == "Other":
                boilerplate_sentences += 1
                break

    total_sentences = len(data)
    boilerplate_sentences_percentage = (
        (boilerplate_sentences / total_sentences) * 100 if total_sentences > 0 else 0
    )

    return BoilerplateInformation(
        boilerplate_sentences=boilerplate_sentences,
        boilerplate_sentences_percentage=boilerplate_sentences_percentage,
    )


# --------------- Summary Report -----------------


@dataclass
class SummaryReport:
    """Summary report of a privacy policy analysis."""

    policy: PolicyInformation
    context: ContextInformation
    purpose: PurposeInformation
    data_type: DataTypeInformation
    processing: ProcessingInformation
    retention: RetentionInformation
    sharing: SharingInformation
    selling: SellingInformation
    security_privacy: SecurityPrivacyInformation
    legal_basis: LegalBasisInformation
    audience: AudienceInformation
    third_party: ThirdPartyInformation
    contact: ContactInformation
    user_rights: UserRightsInformation
    boilerplate: BoilerplateInformation

    @staticmethod
    def from_json(data: dict) -> "SummaryReport":
        return SummaryReport(
            policy=PolicyInformation.from_json(data["policy"]),
            context=ContextInformation.from_json(data["context"]),
            purpose=PurposeInformation.from_json(data["purpose"]),
            data_type=DataTypeInformation.from_json(data["data_type"]),
            processing=ProcessingInformation.from_json(data["processing"]),
            retention=RetentionInformation.from_json(data["retention"]),
            sharing=SharingInformation.from_json(data["sharing"]),
            selling=SellingInformation.from_json(data["selling"]),
            security_privacy=SecurityPrivacyInformation.from_json(
                data["security_privacy"]
            ),
            legal_basis=LegalBasisInformation.from_json(data["legal_basis"]),
            audience=AudienceInformation.from_json(data["audience"]),
            third_party=ThirdPartyInformation.from_json(data["third_party"]),
            contact=ContactInformation.from_json(data["contact"]),
            user_rights=UserRightsInformation.from_json(data["user_rights"]),
            boilerplate=BoilerplateInformation.from_json(data["boilerplate"]),
        )

    def to_json(self) -> dict:
        return asdict(self)


def create_summary_report(
    data: list[StructuredEntry],
    include_contexts: list[str],
    exclude_contexts: list[str],
    data_hierarchy: DataHierarchy = DEFAULT_HIERARCHY,
) -> SummaryReport:
    """Create a summary report from structured data entries."""

    # extract context information before filtering
    context = extract_context_information(data)

    filtered = []
    for entry in data:
        include = False
        for ctx in entry.contexts:
            if include_contexts and ctx in include_contexts:
                include = True
            if exclude_contexts and ctx in exclude_contexts:
                include = False
                break

        if include or (not include_contexts and not exclude_contexts):
            filtered.append(entry)

    data_type = extract_data_type_information(filtered, data_hierarchy)
    processing = extract_processing_information(filtered)
    retention = extract_retention_information(filtered)
    sharing = extract_sharing_information(filtered)
    selling = extract_selling_information(filtered)
    security_privacy = extract_security_privacy_information(filtered)
    legal_basis = extract_legal_basis_information(filtered)
    audience = extract_audience_information(filtered)
    purpose = extract_purpose_information(filtered)
    third_party = extract_third_party_information(filtered)
    policy = extract_change_information(filtered)
    contact = extract_contact_information(filtered)
    user_rights = extract_user_rights_information(filtered)
    boilerplate = extract_boilerplate_information(filtered)

    #
    return SummaryReport(
        policy=policy,
        context=context,
        data_type=data_type,
        processing=processing,
        retention=retention,
        sharing=sharing,
        selling=selling,
        security_privacy=security_privacy,
        legal_basis=legal_basis,
        audience=audience,
        purpose=purpose,
        third_party=third_party,
        contact=contact,
        user_rights=user_rights,
        boilerplate=boilerplate,
    )
