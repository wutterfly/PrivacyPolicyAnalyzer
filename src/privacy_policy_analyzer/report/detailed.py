from dataclasses import dataclass

import pandas as pd

from privacy_policy_analyzer.analysis.structure import (
    Header,
    List,
    StructuredEntry,
    TableCell,
    Text,
)


@dataclass
class PurposeLegalBasis:
    legal_basis: str
    purpose: str

    def __hash__(self):
        return hash((self.legal_basis, self.purpose))


@dataclass
class ThirdParties:
    companies: list[str]
    descriptives: list[str]


@dataclass
class Retention:
    country: list[str]
    storage: list[str]


@dataclass
class Sharing:
    country: list[str]


@dataclass
class DataTypeRow:
    data_type: str
    method_source: list[str]
    purposes_legal_bases: list[PurposeLegalBasis]
    retention: list[str]
    sharing: Sharing
    selling: bool
    third_parties: ThirdParties


@dataclass
class DetailedReport:
    rows: list[DataTypeRow]

    def to_df(self) -> pd.DataFrame:
        data = []
        for row in self.rows:
            data.append(
                {
                    "data_type": row.data_type,
                    "method_source": row.method_source,
                    "purposes_legal_basis": [
                        f"{plb.purpose} -- {plb.legal_basis}"
                        for plb in row.purposes_legal_bases
                    ],
                    "retention": row.retention,
                    "sharing_country": row.sharing.country,
                    "selling": row.selling,
                    "third_party_companies": row.third_parties.companies,
                    "third_party_descriptives": row.third_parties.descriptives,
                }
            )
        return pd.DataFrame(data)


def create_detailed_report(
    data: list[StructuredEntry],
    include_contexts: list[str],
    exclude_contexts: list[str],
) -> DetailedReport:
    rows: dict[str, list[DataTypeRow]] = {
        "Unknown": [],
    }

    for i in range(len(data)):
        prev_entry = data[i - 1] if i > 1 else None
        entry: StructuredEntry = data[i]
        next_entry = data[i + 1] if i + 1 < len(data) else None

        # check current entry include/exclude
        include = False
        for ctx in entry.contexts:
            if exclude_contexts and ctx in exclude_contexts:
                include = False
                break
            if include_contexts and ctx in include_contexts:
                include = True
        if not include:
            continue

        # check previous entry include/exclude
        if prev_entry:
            include = False
            for ctx in prev_entry.contexts:
                if exclude_contexts and ctx in exclude_contexts:
                    prev_entry = None
                    break
                if include_contexts and ctx in include_contexts:
                    include = True

            if not include:
                prev_entry = None

        # check next entry include/exclude
        if next_entry:
            include = False
            for ctx in next_entry.contexts:
                if exclude_contexts and ctx in exclude_contexts:
                    next_entry = None
                    break
                if include_contexts and ctx in include_contexts:
                    include = True

            if not include:
                next_entry = None

        for tpc in entry.topics:
            data_types: list[str] = []
            method_source: list[str] = []
            legal_basis: list[str] = []
            purpose: list[str] = []
            sharing = Sharing(country=[])
            retention = Retention(country=[], storage=[])
            third_parties = ThirdParties(companies=[], descriptives=[])
            privacy_modifier = []

            not_modifier = False

            if tpc.topic == "Processing":
                skip = any(cnt.content == "NotProcessing" for cnt in tpc.contents)
                if skip:
                    not_modifier = True
                    continue

                for cnt in tpc.contents:
                    if cnt.content == "DataType":
                        data_types.extend(cnt.attributes)
                    elif cnt.content == "Method/Source":
                        method_source.extend(cnt.attributes)
                    elif cnt.content == "Tracking/Conversion":
                        data_types.extend(cnt.attributes)
                    elif cnt.content == "Profiling":
                        if not any(attr == "NotProfiling" for attr in cnt.attributes):
                            data_types.append("Profiling")
                        else:
                            not_modifier = True
                    elif cnt.content == "AutomatedDecisionMaking":
                        if not any(
                            attr == "NoAutomatedDecisionMaking"
                            for attr in cnt.attributes
                        ):
                            data_types.append("AutomatedDecisionMaking")
                        else:
                            not_modifier = True
            elif tpc.topic == "Retention":
                skip = any(cnt.content == "NoRetention" for cnt in tpc.contents)
                if skip:
                    not_modifier = True
                    continue

                countries = set()

                for cnt in tpc.contents:
                    if cnt.content == "DataType":
                        data_types.extend(cnt.attributes)
                    elif cnt.content == "Country":
                        countries.update(cnt.attributes)

                if "CountriesOutsideOf" in countries:
                    countries = list(countries)
                    countries.remove("CountriesOutsideOf")
                    countries.sort()

                    str_countries = "CountriesOutsideOf(" + ",".join(countries) + ")"
                    retention.country.append(str_countries)
                else:
                    retention.country.extend(countries)
            elif tpc.topic == "Deletion":
                for cnt in tpc.contents:
                    if cnt.content == "DataType":
                        data_types.extend(cnt.attributes)
            elif tpc.topic == "Sharing":
                skip = any(cnt.content == "NotStated" for cnt in tpc.contents)
                if skip:
                    not_modifier = True
                    continue

                countries = set()

                for cnt in tpc.contents:
                    if cnt.content == "DataType":
                        data_types.extend(cnt.attributes)
                    elif cnt.content == "Country":
                        countries.update(cnt.attributes)

                if "CountriesOutsideOf" in countries:
                    countries = list(countries)
                    countries.remove("CountriesOutsideOf")
                    countries.sort()

                    str_countries = "CountriesOutsideOf(" + ",".join(countries) + ")"
                    retention.country.append(str_countries)
                else:
                    retention.country.extend(countries)
            elif tpc.topic == "Selling":
                skip = any(cnt.content == "NotSelling" for cnt in tpc.contents)
                if skip:
                    not_modifier = True
                    continue

                for cnt in tpc.contents:
                    if cnt.content == "DataType":
                        data_types.extend(cnt.attributes)
            elif tpc.topic == "LegalBasis":
                for cnt in tpc.contents:
                    legal_basis.append(cnt.content)
            elif tpc.topic == "Purpose":
                for cnt in tpc.contents:
                    purpose.append(cnt.content)
                    if cnt.content in [
                        "ProvideService",
                        "ProvideProduct",
                        "Communication",
                    ]:
                        purpose.extend(cnt.attributes)
            elif tpc.topic == "ThirdParty":
                for cnt in tpc.contents:
                    if cnt.content == "Company":
                        third_parties.companies.extend(cnt.attributes)
                    elif cnt.content == "Descriptive":
                        third_parties.descriptives.extend(cnt.attributes)
            elif tpc.topic == "Security/Privacy":
                for cnt in tpc.contents:
                    if cnt.content == "TechnicalPrivacyMeasures":
                        privacy_modifier.extend(cnt.attributes)

            # Skip if something is not done
            if not_modifier:
                continue

            #  Determine neighboring entries' structures
            curr_structure = entry.structure
            if isinstance(curr_structure, Header):
                prev_entry = None
                next_entry = None

            if isinstance(curr_structure, TableCell):
                prev_entry = None
                next_entry = None

            if isinstance(curr_structure, List):
                prev_entry = None
                next_entry = None

            if isinstance(curr_structure, Text):
                if prev_entry and not isinstance(prev_entry.structure, Text):
                    prev_entry = None
                if next_entry and not isinstance(next_entry.structure, Text):
                    next_entry = None

            # Fill in missing purpose and legal_basis from neighboring entries

            if prev_entry and data_types and not purpose:
                for tpc in prev_entry.topics:
                    if tpc.topic == "Purpose":
                        for cnt in tpc.contents:
                            purpose.append(cnt.content)
                            if cnt.content in ["ProvideService", "Communication"]:
                                purpose.extend(cnt.attributes)
                    elif tpc.topic == "LegalBasis":
                        for cnt in tpc.contents:
                            legal_basis.append(cnt.content)

            if next_entry and data_types and not purpose:
                for tpc in data[i + 1].topics:
                    if tpc.topic == "Purpose":
                        for cnt in tpc.contents:
                            purpose.append(cnt.content)
                            if cnt.content in ["ProvideService", "Communication"]:
                                purpose.extend(cnt.attributes)
                    elif tpc.topic == "LegalBasis":
                        for cnt in tpc.contents:
                            legal_basis.append(cnt.content)

            if not data_types:
                data_types = ["Unknown"]

            if privacy_modifier:
                data_types = [
                    f"{pm}({dt})" for dt in data_types for pm in privacy_modifier
                ]

            if not legal_basis:
                legal_basis = ["NotStated"]

            if not purpose:
                purpose = ["NotStated"]

            if legal_basis == ["NotStated"] and purpose == ["NotStated"]:
                legal_basis = []
                purpose = []

            for data_type in data_types:
                plb = [PurposeLegalBasis(lb, p) for lb in legal_basis for p in purpose]
                row = DataTypeRow(
                    data_type=data_type,
                    method_source=method_source,
                    purposes_legal_bases=plb,
                    retention=retention.country,
                    sharing=sharing,
                    selling=any(
                        tpc.topic == "Selling"
                        and not any(cnt.content == "NotSelling" for cnt in tpc.contents)
                        for tpc in entry.topics
                    ),
                    third_parties=third_parties,
                )
                if data_type not in rows:
                    rows[data_type] = []

                rows[data_type].append(row)

    # compact rows by data_type

    rows_compacted: list[DataTypeRow] = []
    for data_type, row_list in rows.items():
        combined_method_source: set[str] = set()
        combined_purposes_legal_bases: set[PurposeLegalBasis] = set()
        combined_retention: set[str] = set()
        combined_sharing_countries: set[str] = set()
        combined_selling = False
        combined_third_parties_companies: set[str] = set()
        combined_third_parties_descriptives: set[str] = set()

        for row in row_list:
            combined_method_source.update(row.method_source)
            combined_purposes_legal_bases.update(row.purposes_legal_bases)
            combined_retention.update(row.retention)
            combined_sharing_countries.update(row.sharing.country)
            combined_selling = combined_selling or row.selling
            combined_third_parties_companies.update(row.third_parties.companies)
            combined_third_parties_descriptives.update(row.third_parties.descriptives)

        combined_row = DataTypeRow(
            data_type=data_type,
            method_source=list(combined_method_source),
            purposes_legal_bases=list(combined_purposes_legal_bases),
            retention=list(combined_retention),
            sharing=Sharing(country=list(combined_sharing_countries)),
            selling=combined_selling,
            third_parties=ThirdParties(
                companies=list(combined_third_parties_companies),
                descriptives=list(combined_third_parties_descriptives),
            ),
        )
        rows_compacted.append(combined_row)

    return DetailedReport(rows=rows_compacted)
