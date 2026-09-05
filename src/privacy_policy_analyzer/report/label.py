from dataclasses import dataclass

from privacy_policy_analyzer.report.readability import (
    ReadabilityScores,
    fre_score_mapping,
)
from privacy_policy_analyzer.report.score import ScoreReport, TransparencyScore
from privacy_policy_analyzer.report.summary import (
    LegalBasisInformation,
    PurposeInformation,
    SecurityPrivacyInformation,
    SummaryReport,
    UserRightsInformation,
)


@dataclass
class LabelConfig:
    """Configuration for generating the SVG label, controlling what section to include."""

    grade_data_specificity: bool = True
    grade_third_party_specificity: bool = True
    grade_retention_specificity: bool = True
    grade_readability: bool = True

    collection_purposes: bool = True
    coverage_security_measures: bool = True
    coverage_user_rights: bool = True
    coverage_merger_acquisition: bool = True
    coverage_children: bool = True
    coverage_overall: bool = True

    contact_info: bool = True
    meta_info: bool = True
    meta_overall: bool = True

    profiling: bool = True
    automated_decision: bool = True
    total_collected_data_types: bool = True
    specific_data_types_collected: bool = True

    total_shared_data_types: bool = True
    specific_shared_data_types: bool = True

    total_third_parties: bool = True
    specific_third_parties: bool = True

    total_third_party_types: bool = True
    specific_third_party_types: bool = True

    legal_basis: bool = True


DEFAULT_LABEL_CONFIG = LabelConfig()


def _count_user_rights(data: UserRightsInformation) -> tuple[int, int]:
    """Count true values in a dictionary. Returns (true_count, total_count)."""
    true_count = 0
    total_count = 0

    true_count += 1 if data.access is True else 0
    true_count += 1 if data.rectification is True else 0
    true_count += 1 if data.deletion is True else 0
    true_count += 1 if data.restriction is True else 0
    true_count += 1 if data.data_portability is True else 0
    true_count += 1 if data.object is True else 0
    true_count += 1 if data.revoke is True else 0
    true_count += 1 if data.complain is True else 0

    total_count = 8
    if data.no_discrimination is not None:
        true_count += 1 if data.no_discrimination is True else 0
        total_count += 1

    return true_count, total_count


def _get_checkmark_symbol(value: bool | None) -> tuple[str, str]:
    """Get the symbol and CSS class for a boolean/null value."""
    if value is None:
        return "?", "unknown"
    elif value is True:
        return "✓", "yes"
    else:
        return "✗", "no"


def _get_checkmark_symbol_inverted(value: bool | None) -> tuple[str, str]:
    """Get the symbol and CSS class for a boolean/null value, with inverted logic."""
    if value is None:
        return "?", "unknown"
    elif value is True:
        return "✓", "no"
    else:
        return "✗", "yes"


def _get_score_color(score: float) -> str:
    """Get color based on score."""

    if score > 60:
        return "#4CAF50"  # Green
    elif score > 30:
        return "#FFC107"  # Amber
    else:
        return "#F44336"  # Red


def _format_purposes(purposes: list[str], max_display: int) -> list[str]:
    """Format purpose list, limiting to max_display items."""
    formatted = []
    for purpose in purposes[:max_display]:
        # Convert CamelCase to spaced words
        spaced = "".join([" " + c if c.isupper() else c for c in purpose]).strip()
        formatted.append(spaced)

    if len(purposes) > max_display:
        formatted.append(f"And {len(purposes) - max_display} more...")

    return formatted


def _generate_svg_header(total_height: int) -> str:
    """Generate SVG header with styles."""
    header = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 {total_height}" width="400" height="{total_height}">\n'
    header += """  <defs>
    <style>
      .title { font-family: Arial, sans-serif; font-size: 24px; font-weight: bold; }
      .section-title { font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; }
      .label { font-family: Arial, sans-serif; font-size: 12px; }
      .value { font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; }
      .small { font-family: Arial, sans-serif; font-size: 10px; }
      .grade-a { fill: #4CAF50; }
      .grade-b { fill: #8BC34A; }
      .grade-c { fill: #FFC107; }
      .grade-d { fill: #FF9800; }
      .grade-e { fill: #FF5722; }
      .grade-f { fill: #F44336; }
      .grade-neutral { fill: #9E9E9E; }
      .grade-unknown { fill: #9E9E9E; }
      .yes { fill: #4CAF50; }
      .no { fill: #F44336; }
      .unknown { fill: #FFC107; }
      .partial { fill: #FFC107; }
    </style>
  </defs>

"""
    header += "  <!-- Background -->\n"
    header += f'  <rect width="400" height="{total_height}" fill="#ffffff" stroke="#000000" stroke-width="2"/>\n'
    header += """
  <!-- Title -->
  <text x="200" y="35" text-anchor="middle" class="title">Privacy Policy Summary</text>
  <line x1="20" y1="45" x2="380" y2="45" stroke="#000000" stroke-width="3"/>
"""
    return header


def _generate_transparency_section(
    transparency: TransparencyScore,
    readability_score: float,
    y_pos: int,
    config: LabelConfig,
) -> tuple[str, int]:
    """Generate the transparency section."""
    data_specificity_grade = transparency.data_specificity_grade
    third_party_specificity_grade = (
        transparency.third_party_specificity_grade
        if transparency.third_party_specificity_grade
        else "unknown"
    )
    retention_specificity_grade = transparency.retention_specificity_grade

    _, score = fre_score_mapping(readability_score)

    section = f"""
  <!-- Transparency Section -->
  <text x="20" y="{y_pos}" class="section-title">Transparency</text>
  <line x1="20" y1="{y_pos + 5}" x2="380" y2="{y_pos + 5}" stroke="#000000" stroke-width="1"/>

"""

    row_height = 20
    cur_y = y_pos + 20

    if config.grade_data_specificity:
        section += (
            f'  <text x="30" y="{cur_y + 5}" class="label">Data Specificity:</text>\n'
        )
        section += f'  <circle cx="360" cy="{cur_y + 1}" r="10" class="grade-{data_specificity_grade.lower()}"/>\n'
        section += f'  <text x="360" y="{cur_y + 4}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{data_specificity_grade}</text>\n'
        section += "  \n"
        cur_y += row_height

    if config.grade_third_party_specificity:
        section += f'  <text x="30" y="{cur_y + 5}" class="label">Third Party Specificity:</text>\n'
        section += f'  <circle cx="360" cy="{cur_y + 1}" r="10" class="grade-{third_party_specificity_grade.lower()}"/>\n'
        section += f'  <text x="360" y="{cur_y + 4}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{third_party_specificity_grade}</text>\n'
        section += "  \n"
        cur_y += row_height

    if config.grade_retention_specificity:
        section += f'  <text x="30" y="{cur_y + 5}" class="label">Retention Specificity:</text>\n'
        section += f'  <circle cx="360" cy="{cur_y + 1}" r="10" class="grade-{retention_specificity_grade.lower()}"/>\n'
        section += f'  <text x="360" y="{cur_y + 4}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{retention_specificity_grade}</text>\n'
        section += "  \n"
        cur_y += row_height

    if config.grade_readability:
        section += f'  <text x="30" y="{cur_y + 5}" class="label">Readability Score:</text>\n'
        section += (
            f'  <circle cx="360" cy="{cur_y + 1}" r="10" class="grade-neutral"/>\n'
        )
        section += f'  <text x="360" y="{cur_y + 4}" text-anchor="middle" fill="White" style="font-size: 10px; font-weight: bold;">{score}</text>\n'
        cur_y += row_height

    return section, cur_y + 20


def _generate_purposes_section(
    info: PurposeInformation, y_offset: int
) -> tuple[str, int]:
    """Generate the purposes section. Returns (svg_string, final_y_position)."""
    display = 7
    formatted_purposes = _format_purposes(info.purposes, display)
    formatted_third_party_purposes = _format_purposes(
        info.third_party_purposes, display
    )
    max_purposes = max(len(formatted_purposes), len(formatted_third_party_purposes))

    section = """
  <!-- Purposes Section -->
"""
    section += f'  <text x="20" y="{y_offset}" class="section-title">Data Collection Purposes</text>\n'
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 25}" class="label">Primary Purposes:</text>\n'
    )
    section += f'  <text x="210" y="{y_offset + 25}" class="label">Third Party Purposes:</text>\n'

    # Add purpose items
    y_pos = y_offset + 42
    for i in range(max_purposes):
        if i < len(formatted_purposes):
            section += f'  <text x="30" y="{y_pos}" class="small">  • {formatted_purposes[i]}</text>\n'
        if i < len(formatted_third_party_purposes):
            section += f'  <text x="210" y="{y_pos}" class="small">  • {formatted_third_party_purposes[i]}</text>\n'
        y_pos += 15

    return section, y_pos + 23


def _generate_coverage_section(
    y_offset: int,
    security_privacy: SecurityPrivacyInformation,
    rights_count: int,
    rights_total: int,
    merger_acquisition: bool,
    children_mentioned: bool,
    coverage_score: float,
    config: LabelConfig,
) -> tuple[str, int]:
    """Generate the coverage section. Returns (svg_string, final_y_position)."""
    coverage_bar_width = coverage_score * 3.4
    coverage_color = _get_score_color(coverage_score)

    merger_symbol, merger_class = _get_checkmark_symbol(merger_acquisition)
    children_symbol, children_class = _get_checkmark_symbol(children_mentioned)

    sec_count = [
        security_privacy.transmission,
        security_privacy.physical,
        security_privacy.organizational,
        security_privacy.technical > 0,
        security_privacy.contractual > 0,
    ].count(True)

    section = """
  <!-- Coverage Section -->
"""
    section += (
        f'  <text x="20" y="{y_offset}" class="section-title">Policy Coverage</text>\n'
    )
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"

    row_height = 20
    cur_y = y_offset + 5

    if config.coverage_security_measures:
        cur_y += row_height
        section += (
            f'  <text x="30" y="{cur_y}" class="label">Security Measures:</text>\n'
        )
        section += f'  <text x="350" y="{cur_y}" text-anchor="end" class="value">{sec_count}/5</text>\n'
        section += "  \n"

    if config.coverage_user_rights:
        cur_y += row_height
        section += f'  <text x="30" y="{cur_y}" class="label">User Rights:</text>\n'
        section += f'  <text x="350" y="{cur_y}" text-anchor="end" class="value">{rights_count}/{rights_total}</text>\n'
        section += "  \n"

    if config.coverage_merger_acquisition or config.coverage_children:
        cur_y += row_height
        if config.coverage_merger_acquisition:
            section += f'  <text x="30" y="{cur_y}" class="label">Merger/Acquisition Info:</text>\n'
            section += (
                f'  <circle cx="175" cy="{cur_y - 4}" r="8" class="{merger_class}"/>\n'
            )
            section += f'  <text x="175" y="{cur_y - 1}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{merger_symbol}</text>\n'
            section += "  \n"
        if config.coverage_children:
            # take the left slot if merger/acquisition isn't shown to occupy it
            label_x, circle_cx = (
                (203, 360) if config.coverage_merger_acquisition else (30, 175)
            )
            section += f'  <text x="{label_x}" y="{cur_y}" class="label">Children\'s Data Mentioned:</text>\n'
            section += f'  <circle cx="{circle_cx}" cy="{cur_y - 4}" r="8" class="{children_class}"/>\n'
            section += f'  <text x="{circle_cx}" y="{cur_y - 1}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{children_symbol}</text>\n'
            section += "  \n"

    if config.coverage_overall:
        cur_y += 20
        section += f'  <rect x="30" y="{cur_y}" width="340" height="20" fill="#e0e0e0" rx="3"/>\n'
        section += f'  <rect x="30" y="{cur_y}" width="{coverage_bar_width}" height="20" fill="{coverage_color}" rx="3"/>\n'
        section += f'  <text x="200" y="{cur_y + 14}" text-anchor="middle" class="value" fill="#333">Overall Coverage: {coverage_score:.2f}%</text>\n'
        cur_y += 45  # bar height (20) + gap before next section heading (25)
    else:
        cur_y += 20

    return section, cur_y


def _generate_contact_meta_section(
    y_offset: int,
    contact_phone: bool,
    contact_email: bool,
    contact_address: bool,
    contact_website: bool,
    policy_date_available: bool,
    dpo: bool,
    meta_score: float,
    config: LabelConfig,
) -> tuple[str, int]:
    """Generate the contact & meta information section. Returns (svg_string, final_y_position)."""
    meta_bar_width = meta_score * 3.4
    meta_color = _get_score_color(meta_score)

    phone_symbol, phone_class = _get_checkmark_symbol(contact_phone)
    email_symbol, email_class = _get_checkmark_symbol(contact_email)
    address_symbol, address_class = _get_checkmark_symbol(contact_address)
    website_symbol, website_class = _get_checkmark_symbol(contact_website)
    date_symbol, date_class = _get_checkmark_symbol(policy_date_available)
    dpo_symbol, dpo_class = _get_checkmark_symbol(dpo)

    section = """
  <!-- Meta Information Section -->
"""
    section += f'  <text x="20" y="{y_offset}" class="section-title">Contact &amp; Meta Information</text>\n'
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"

    row_height = 17
    cur_y = y_offset + 8

    def _left(label: str, cls: str, symbol: str) -> str:
        row = f'  <text x="30" y="{cur_y}" class="label">{label}</text>\n'
        row += f'  <circle cx="175" cy="{cur_y - 4}" r="8" class="{cls}"/>\n'
        row += f'  <text x="175" y="{cur_y - 1}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{symbol}</text>\n'
        return row + "  \n"

    def _right(label: str, cls: str, symbol: str) -> str:
        row = f'  <text x="210" y="{cur_y}" class="label">{label}</text>\n'
        row += f'  <circle cx="360" cy="{cur_y - 4}" r="8" class="{cls}"/>\n'
        row += f'  <text x="360" y="{cur_y - 1}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{symbol}</text>\n'
        return row + "  \n"

    if config.contact_info and config.meta_info:
        # phone/date and email/dpo paired, one pair per row
        cur_y += row_height
        section += _left("Contact Phone:", phone_class, phone_symbol)
        section += _right("Policy Date:", date_class, date_symbol)

        cur_y += row_height
        section += _left("Contact Email:", email_class, email_symbol)
        section += _right("Data Protection Officer:", dpo_class, dpo_symbol)

    elif config.contact_info:
        cur_y += row_height
        section += _left("Contact Phone:", phone_class, phone_symbol)

        cur_y += row_height
        section += _left("Contact Email:", email_class, email_symbol)

    elif config.meta_info:
        # no contact fields taking the left slots, so pair date/dpo together
        cur_y += row_height
        section += _left("Policy Date:", date_class, date_symbol)
        section += _right("Data Protection Officer:", dpo_class, dpo_symbol)

    if config.contact_info:
        cur_y += row_height
        section += _left("Contact Address:", address_class, address_symbol)

        cur_y += row_height
        section += _left("Contact Website:", website_class, website_symbol)

    if config.meta_overall:
        cur_y += 10
        section += f'  <rect x="30" y="{cur_y}" width="340" height="20" fill="#e0e0e0" rx="3"/>\n'
        section += f'  <rect x="30" y="{cur_y}" width="{meta_bar_width}" height="20" fill="{meta_color}" rx="3"/>\n'
        section += f'  <text x="200" y="{cur_y + 14}" text-anchor="middle" class="value" fill="#333">Overall: {meta_score:.2f}%</text>\n'
        cur_y += 45  # bar height (20) + gap before next section heading (25)
    else:
        cur_y += 20

    return section, cur_y


def _generate_data_processing_section(
    y_offset: int,
    profiling: bool | None,
    automated_decision: bool | None,
    data_types_count: int,
    categories_display: list[str],
    config: LabelConfig,
) -> tuple[str, int]:
    """Generate the data processing summary section. Returns (svg_string, final_y_position)."""

    profiling_symbol, profiling_class = _get_checkmark_symbol_inverted(profiling)
    automated_symbol, automated_class = _get_checkmark_symbol_inverted(
        automated_decision
    )

    section = """
  <!-- Data Processing Summary -->
"""
    section += f'  <text x="20" y="{y_offset}" class="section-title">Data Processing Summary</text>\n'
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"

    row_height = 20
    cur_y = y_offset + 5

    if config.profiling or config.automated_decision:
        cur_y += row_height
        if config.profiling:
            section += f'  <text x="30" y="{cur_y}" class="label">Profiling:</text>\n'
            section += f'  <circle cx="175" cy="{cur_y - 4}" r="8" class="{profiling_class}"/>\n'
            section += f'  <text x="175" y="{cur_y - 1}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{profiling_symbol}</text>\n'
            section += "  \n"
        if config.automated_decision:
            # take the left slot if profiling isn't shown to occupy it
            label_x, circle_cx = (210, 360) if config.profiling else (30, 175)
            section += f'  <text x="{label_x}" y="{cur_y}" class="label">Automated Decision:</text>\n'
            section += f'  <circle cx="{circle_cx}" cy="{cur_y - 4}" r="8" class="{automated_class}"/>\n'
            section += f'  <text x="{circle_cx}" y="{cur_y - 1}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{automated_symbol}</text>\n'
            section += "  \n"

    if config.total_collected_data_types:
        cur_y += row_height
        section += f'  <text x="30" y="{cur_y}" class="label">Total Data Types Collected:</text>\n'
        section += f'  <text x="350" y="{cur_y}" text-anchor="end" class="value">{data_types_count}</text>\n'
        section += "  \n"

    if config.specific_data_types_collected and categories_display:
        cur_y += 20
        section += f'  <text x="30" y="{cur_y}" class="small">Including: {categories_display[0]}</text>\n'
        for i in range(1, len(categories_display)):
            cur_y += 15
            section += f'  <text x="30" y="{cur_y}" class="small">{categories_display[i]}</text>\n'
        cur_y += 23
    else:
        cur_y += 15

    return section, cur_y


def _generate_data_sharing_section(
    y_offset: int,
    sharing_types: list[str],
    total_sharing_types: int,
    companies: list[str],
    total_companies: int,
    descriptives: list[str],
    total_descriptives: int,
    config: LabelConfig,
) -> tuple[str, int]:
    """Generate the data sharing section. Returns (svg_string, final_y_position)."""

    section = """
  <!-- Data Sharing -->
"""
    section += (
        f'  <text x="20" y="{y_offset}" class="section-title">Data Sharing</text>\n'
    )
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"

    cur_y = y_offset + 5

    # Shared Data Types
    if config.total_shared_data_types or config.specific_shared_data_types:
        cur_y += 20
        section += (
            f'  <text x="30" y="{cur_y}" class="label">Shared Data Types:</text>\n'
        )
        if config.total_shared_data_types:
            section += f'  <text x="350" y="{cur_y}" text-anchor="end" class="value">{total_sharing_types}</text>\n'
        section += "  \n"

        if config.specific_shared_data_types and sharing_types:
            cur_y += 17
            section += (
                f'  <text x="30" y="{cur_y}" class="small">{sharing_types[0]}</text>\n'
            )
            for i in range(1, len(sharing_types)):
                cur_y += 15
                section += f'  <text x="30" y="{cur_y}" class="small">{sharing_types[i]}</text>\n'

    # Third Party Companies
    if config.total_third_parties or config.specific_third_parties:
        cur_y += 20
        section += f'  <text x="30" y="{cur_y}" class="label">Third Parties:</text>\n'
        if config.total_third_parties:
            section += f'  <text x="350" y="{cur_y}" text-anchor="end" class="value">{total_companies} named</text>\n'
        section += "  \n"

        if config.specific_third_parties and companies:
            cur_y += 17
            section += (
                f'  <text x="30" y="{cur_y}" class="small">{companies[0]}</text>\n'
            )
            for i in range(1, len(companies)):
                cur_y += 15
                section += f'  <text x="30" y="{cur_y}" class="small">, {companies[i]}</text>\n'

    # Third Party Descriptives
    if config.total_third_party_types or config.specific_third_party_types:
        cur_y += 20
        section += (
            f'  <text x="30" y="{cur_y}" class="label">Third Party Types:</text>\n'
        )
        if config.total_third_party_types:
            section += f'  <text x="350" y="{cur_y}" text-anchor="end" class="value">{total_descriptives}</text>\n'
        section += "  \n"

        if config.specific_third_party_types and descriptives:
            cur_y += 17
            section += (
                f'  <text x="30" y="{cur_y}" class="small">{descriptives[0]}</text>\n'
            )
            for i in range(1, len(descriptives)):
                cur_y += 15
                section += f'  <text x="30" y="{cur_y}" class="small">{descriptives[i]}</text>\n'

    return section, cur_y + 30


def _generate_legal_basis_section(
    y_offset: int, legal_basis: LegalBasisInformation
) -> tuple[str, int]:
    """Generate the legal basis section with stacked bar chart. Returns (svg_string, final_y_position)."""

    # Get counts for each basis
    total = 0
    basis_data = []

    if legal_basis.consent > 0:
        total += legal_basis.consent
        basis_data.append(("Consent", legal_basis.consent, "#4CAF50"))  # Green

    if legal_basis.contract > 0:
        total += legal_basis.contract
        basis_data.append(("Contract", legal_basis.contract, "#2196F3"))  # Blue

    if legal_basis.legitimate_interest > 0:
        total += legal_basis.legitimate_interest
        basis_data.append(
            ("Legitimate Interest", legal_basis.legitimate_interest, "#FF9800")
        )  # Orange

    if legal_basis.legal_obligation > 0:
        total += legal_basis.legal_obligation
        basis_data.append(
            ("Legal Obligation", legal_basis.legal_obligation, "#9C27B0")
        )  # Purple

    if legal_basis.vital_interests > 0:
        total += legal_basis.vital_interests
        basis_data.append(
            ("Vital Interests", legal_basis.vital_interests, "#F44336")
        )  # Red

    if legal_basis.public_interest > 0:
        total += legal_basis.public_interest
        basis_data.append(
            ("Public Interest", legal_basis.public_interest, "#00BCD4")
        )  # Cyan

    if legal_basis.employment > 0:
        total += legal_basis.employment
        basis_data.append(("Employment", legal_basis.employment, "#795548"))  # Brown

    section = """
  <!-- Legal Basis -->
"""
    section += (
        f'  <text x="20" y="{y_offset}" class="section-title">Legal Basis</text>\n'
    )
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"

    if total == 0:
        # No legal basis mentioned
        section += f'  <text x="30" y="{y_offset + 30}" class="label">No legal basis mentioned in policy</text>\n'
        return section, y_offset + 50

    # Draw stacked bar chart
    bar_width = 340
    bar_height = 30
    bar_x = 30
    bar_y = y_offset + 25

    # Calculate widths for each segment
    current_x = bar_x
    for label, count, color in basis_data:
        segment_width = (count / total) * bar_width

        # Draw segment
        section += f'  <rect x="{current_x}" y="{bar_y}" width="{segment_width}" height="{bar_height}" fill="{color}" rx="2"/>\n'

        # Add count label if segment is wide enough
        if segment_width > 30:
            text_x = current_x + segment_width / 2
            section += f'  <text x="{text_x}" y="{bar_y + bar_height / 2 + 4}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{count}</text>\n'

        current_x += segment_width

    # Add legend below the bar
    legend_y = bar_y + bar_height + 20
    legend_items_per_row = 2
    legend_item_width = 170
    legend_row_height = 20

    for i, (label, count, color) in enumerate(basis_data):
        row = i // legend_items_per_row
        col = i % legend_items_per_row

        legend_x = 30 + (col * legend_item_width)
        legend_item_y = legend_y + (row * legend_row_height)

        # Draw colored square
        section += f'  <rect x="{legend_x}" y="{legend_item_y - 8}" width="10" height="10" fill="{color}" rx="1"/>\n'

        # Draw label
        section += f'  <text x="{legend_x + 15}" y="{legend_item_y}" class="small">{label}: {count}</text>\n'

    # Calculate total height
    total_rows = (len(basis_data) + legend_items_per_row - 1) // legend_items_per_row
    new_y_offset = legend_y + (total_rows * legend_row_height)

    return section, new_y_offset


def _generate_footer(
    y_offset: int, policy_date: str, total_sentences: int, source: str
) -> tuple[str, int]:
    """Generate the footer section."""
    source = source.replace("https://", "").replace("http://", "").strip().rstrip("/")
    footer = """
  <!-- Bottom Border -->
"""
    footer += f'  <line x1="20" y1="{y_offset}" x2="380" y2="{y_offset}" stroke="#000000" stroke-width="3"/>\n'
    footer += "  \n"
    footer += f'  <text x="200" y="{y_offset + 15}" text-anchor="middle" class="small" fill="#666">\n'
    footer += f"    Policy Date: {policy_date} | {total_sentences} sentences\n"
    footer += "  </text>\n"
    footer += f'  <text x="200" y="{y_offset + 30}" text-anchor="middle" class="small" fill="#666">\n'
    footer += f" {source}"
    footer += "  </text>\n"
    footer += "</svg>"

    return footer, y_offset + 38


def display_types(types: list[str], max_len: int) -> list[str]:
    # sort by length (longest first - First Fit Decreasing)
    data_set = sorted(types, key=len, reverse=True)

    bins = []  # Each bin is a list of types
    bin_lengths = []  # Track current length of each bin

    for data in data_set:
        # Try to find an existing bin that can fit this type
        placed = False
        for i, bin_group in enumerate(bins):
            # Calculate length if we add to this bin (account for ", " separator)
            additional_length = len(data) + (2 if bin_group else 0)

            if bin_lengths[i] + additional_length <= max_len:
                bin_group.append(data)
                bin_lengths[i] += additional_length
                placed = True
                break

        # If it doesn't fit in any existing bin, create a new one
        if not placed:
            bins.append([data])
            bin_lengths.append(len(data))

    # Convert bins to comma-separated strings
    return [", ".join(bin_group) for bin_group in bins]


def generate_svg_label(
    scores: ScoreReport,
    summary: SummaryReport,
    readability: ReadabilityScores,
    source: str,
    config: LabelConfig = DEFAULT_LABEL_CONFIG,
) -> str:
    """Generate the complete SVG label from score and summary data."""

    # User rights
    rights_count, rights_total = _count_user_rights(summary.user_rights)

    # Get high-level categories from level 2
    level_2_categories = summary.data_type.data_types_level.get(2, [])
    categories_display_ = display_types(level_2_categories, 65)
    if len(categories_display_) == 0:
        categories_display_ = ["None mentioned"]
    categories_display = categories_display_[:3]
    if len(categories_display_) >= 3:
        last_item = categories_display[-1].split(", ")[-1]
        categories_display[-1] = categories_display[-1].replace(last_item, "and more")

    # Generate all sections first to calculate total height
    svg_parts = []

    # Transparency
    y_pos = 70
    if (
        config.grade_data_specificity
        or config.grade_third_party_specificity
        or config.grade_retention_specificity
        or config.grade_readability
    ):
        transparency_svg, y_pos = _generate_transparency_section(
            scores.transparency, readability.flesh_reading_ease, y_pos, config
        )
        svg_parts.append(transparency_svg)

    # Purposes
    if config.collection_purposes:
        purposes_svg, y_pos = _generate_purposes_section(summary.purpose, y_pos)
        svg_parts.append(purposes_svg)

    # Coverage
    if (
        config.coverage_security_measures
        or config.coverage_user_rights
        or config.coverage_merger_acquisition
        or config.coverage_children
        or config.coverage_overall
    ):
        coverage_svg, y_pos = _generate_coverage_section(
            y_pos,
            summary.security_privacy,
            rights_count,
            rights_total,
            summary.selling.merger_acquisition,
            summary.audience.children,
            scores.coverage.final_score,
            config,
        )
        svg_parts.append(coverage_svg)

    # Contact & Meta
    if config.contact_info or config.meta_info or config.meta_overall:
        contact_svg, y_pos = _generate_contact_meta_section(
            y_pos,
            summary.contact.phone,
            summary.contact.email,
            summary.contact.address,
            summary.contact.website,
            summary.policy.date is not None,
            summary.policy.data_protection_officer,
            scores.meta.final_score,
            config,
        )
        svg_parts.append(contact_svg)

    # Data Processing
    if (
        config.profiling
        or config.automated_decision
        or config.total_collected_data_types
        or config.specific_data_types_collected
    ):
        processing_svg, y_pos = _generate_data_processing_section(
            y_pos,
            summary.processing.profiling,
            summary.processing.automated_decision,
            len(summary.data_type.data_types),
            categories_display,
            config,
        )
        svg_parts.append(processing_svg)

    # Third Party Descriptive
    descriptives_ = display_types(summary.third_party.descriptives, 65)
    if len(descriptives_) == 0:
        descriptives_ = ["None mentioned"]
    descriptives = descriptives_[:2]
    if len(descriptives_) >= 2:
        last_item = descriptives[-1].split(", ")[-1]
        descriptives[-1] = descriptives[-1].replace(last_item, "and more")

    # Data Sharing Types
    sharing_types_ = display_types(summary.sharing.sharing_types, 65)
    if len(sharing_types_) == 0:
        sharing_types_ = ["None mentioned"]
    sharing_types = sharing_types_[:2]
    if len(sharing_types_) >= 2:
        last_item = sharing_types[-1].split(", ")[-1]
        sharing_types[-1] = sharing_types[-1].replace(last_item, "and more")

    # Companies
    companies_ = display_types(summary.third_party.companies, 65)
    if len(companies_) == 0:
        companies_ = ["None mentioned"]
    companies = companies_[:2]
    if len(companies_) >= 2:
        last_item = companies[-1].split(", ")[-1]
        companies[-1] = companies[-1].replace(last_item, "and more")

    if (
        config.total_shared_data_types
        or config.specific_shared_data_types
        or config.total_third_parties
        or config.specific_third_parties
        or config.total_third_party_types
        or config.specific_third_party_types
    ):
        sharing_svg, y_pos = _generate_data_sharing_section(
            y_pos,
            sharing_types,
            len(summary.sharing.sharing_types),
            companies,
            len(summary.third_party.companies),
            descriptives,
            len(summary.third_party.descriptives),
            config,
        )
        svg_parts.append(sharing_svg)

    # Legal Basis
    if config.legal_basis:
        legal_svg, y_pos = _generate_legal_basis_section(y_pos, summary.legal_basis)
        svg_parts.append(legal_svg)

    # Footer
    footer_svg, y_pos = _generate_footer(
        y_pos,
        "unknown" if summary.policy.date is None else summary.policy.date,
        summary.policy.total_sentences,
        source,
    )
    svg_parts.append(footer_svg)

    # Calculate total height from final y position (add space for footer)
    total_height = y_pos

    # Insert header at the beginning
    svg_content = _generate_svg_header(total_height) + "".join(svg_parts)

    return svg_content
