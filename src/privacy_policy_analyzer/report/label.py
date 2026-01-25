from privacy_policy_analyzer.report.score import ScoreReport, TransparencyScore
from privacy_policy_analyzer.report.summary import (
    LegalBasisInformation,
    PurposeInformation,
    SecurityPrivacyInformation,
    SummaryReport,
    UserRightsInformation,
)


def count_user_rights(data: UserRightsInformation) -> tuple[int, int]:
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


def get_checkmark_symbol(value: bool | None) -> tuple[str, str]:
    """Get the symbol and CSS class for a boolean/null value."""
    if value is None:
        return "?", "unknown"
    elif value is True:
        return "✓", "yes"
    else:
        return "✗", "no"


def get_score_color(score: float) -> str:
    """Get color based on score."""

    if score > 60:
        return "#4CAF50"  # Green
    elif score > 30:
        return "#FFC107"  # Amber
    else:
        return "#F44336"  # Red


def format_purposes(purposes: list[str], max_display: int) -> list[str]:
    """Format purpose list, limiting to max_display items."""
    formatted = []
    for purpose in purposes[:max_display]:
        # Convert CamelCase to spaced words
        spaced = "".join([" " + c if c.isupper() else c for c in purpose]).strip()
        formatted.append(spaced)

    if len(purposes) > max_display:
        formatted.append(f"And {len(purposes) - max_display} more...")

    return formatted


def generate_svg_header(total_height: int) -> str:
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
      .grade-f { fill: #F44336; }
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


def generate_transparency_section(transparency: TransparencyScore) -> str:
    """Generate the transparency section."""
    data_specificity_grade = transparency.data_specificity_grade
    third_party_specificity_grade = (
        transparency.third_party_specificity_grade
        if transparency.third_party_specificity_grade
        else "unknown"
    )
    retention_specificity_grade = transparency.retention_specificity_grade

    section = """
  <!-- Transparency Section -->
  <text x="20" y="70" class="section-title">Transparency</text>
  <line x1="20" y1="75" x2="380" y2="75" stroke="#000000" stroke-width="1"/>

"""
    section += '  <text x="30" y="95" class="label">Data Specificity:</text>\n'
    section += f'  <circle cx="360" cy="91" r="10" class="grade-{data_specificity_grade.lower()}"/>\n'
    section += f'  <text x="360" y="94" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{data_specificity_grade}</text>\n'
    section += "  \n"
    section += '  <text x="30" y="115" class="label">Third Party Specificity:</text>\n'
    section += f'  <circle cx="360" cy="111" r="10" class="grade-{third_party_specificity_grade.lower()}"/>\n'
    section += f'  <text x="360" y="114" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{third_party_specificity_grade}</text>\n'
    section += "  \n"
    section += '  <text x="30" y="135" class="label">Retention Specificity:</text>\n'
    section += f'  <circle cx="360" cy="131" r="10" class="grade-{retention_specificity_grade.lower()}"/>\n'
    section += f'  <text x="360" y="134" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{retention_specificity_grade}</text>\n'

    return section


def generate_purposes_section(info: PurposeInformation) -> tuple[str, int]:
    """Generate the purposes section. Returns (svg_string, final_y_position)."""
    display = 7
    formatted_purposes = format_purposes(info.purposes, display)
    formatted_third_party_purposes = format_purposes(info.third_party_purposes, display)
    max_purposes = max(len(formatted_purposes), len(formatted_third_party_purposes))

    y_offset = 170
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

    return section, y_pos


def generate_coverage_section(
    y_offset: int,
    security_privacy: SecurityPrivacyInformation,
    rights_count: int,
    rights_total: int,
    merger_acquisition: bool,
    children_mentioned: bool,
    coverage_score: float,
) -> tuple[str, int]:
    """Generate the coverage section. Returns (svg_string, final_y_position)."""
    coverage_bar_width = coverage_score * 3.4
    coverage_color = get_score_color(coverage_score)

    merger_symbol, merger_class = get_checkmark_symbol(merger_acquisition)
    children_symbol, children_class = get_checkmark_symbol(children_mentioned)

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
    section += (
        f'  <text x="30" y="{y_offset + 25}" class="label">Security Measures:</text>\n'
    )
    section += f'  <text x="350" y="{y_offset + 25}" text-anchor="end" class="value">{sec_count}/5</text>\n'
    section += "  \n"
    section += f'  <text x="30" y="{y_offset + 42}" class="label">User Rights:</text>\n'
    section += f'  <text x="350" y="{y_offset + 42}" text-anchor="end" class="value">{rights_count}/{rights_total}</text>\n'
    section += "  \n"
    section += f'  <text x="30" y="{y_offset + 62}" class="label">Merger/Acquisition Info:</text>\n'
    section += (
        f'  <circle cx="175" cy="{y_offset + 58}" r="8" class="{merger_class}"/>\n'
    )
    section += f'  <text x="175" y="{y_offset + 61}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{merger_symbol}</text>\n'
    section += "  \n"
    section += f'  <text x="203" y="{y_offset + 62}" class="label">Children\'s Data Mentioned:</text>\n'
    section += (
        f'  <circle cx="360" cy="{y_offset + 58}" r="8" class="{children_class}"/>\n'
    )
    section += f'  <text x="360" y="{y_offset + 61}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{children_symbol}</text>\n'
    section += "  \n"
    section += f'  <rect x="30" y="{y_offset + 72}" width="340" height="20" fill="#e0e0e0" rx="3"/>\n'
    section += f'  <rect x="30" y="{y_offset + 72}" width="{coverage_bar_width}" height="20" fill="{coverage_color}" rx="3"/>\n'
    section += f'  <text x="200" y="{y_offset + 86}" text-anchor="middle" class="value" fill="#333">Overall Coverage: {coverage_score:.2f}%</text>\n'

    return section, y_offset + 117


def generate_contact_meta_section(
    y_offset: int,
    contact_phone: bool,
    contact_email: bool,
    contact_address: bool,
    contact_website: bool,
    policy_date_available: bool,
    dpo: bool,
    meta_score: float,
) -> tuple[str, int]:
    """Generate the contact & meta information section. Returns (svg_string, final_y_position)."""
    meta_bar_width = meta_score * 3.4
    meta_color = get_score_color(meta_score)

    phone_symbol, phone_class = get_checkmark_symbol(contact_phone)
    email_symbol, email_class = get_checkmark_symbol(contact_email)
    address_symbol, address_class = get_checkmark_symbol(contact_address)
    website_symbol, website_class = get_checkmark_symbol(contact_website)
    date_symbol, date_class = get_checkmark_symbol(policy_date_available)
    dpo_symbol, dpo_class = get_checkmark_symbol(dpo)

    section = """
  <!-- Meta Information Section -->
"""
    section += f'  <text x="20" y="{y_offset}" class="section-title">Contact &amp; Meta Information</text>\n'
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 25}" class="label">Contact Phone:</text>\n'
    )
    section += (
        f'  <circle cx="175" cy="{y_offset + 21}" r="8" class="{phone_class}"/>\n'
    )
    section += f'  <text x="175" y="{y_offset + 24}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{phone_symbol}</text>\n'
    section += "  \n"
    section += (
        f'  <text x="210" y="{y_offset + 25}" class="label">Policy Date:</text>\n'
    )
    section += f'  <circle cx="360" cy="{y_offset + 21}" r="8" class="{date_class}"/>\n'
    section += f'  <text x="360" y="{y_offset + 24}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{date_symbol}</text>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 42}" class="label">Contact Email:</text>\n'
    )
    section += (
        f'  <circle cx="175" cy="{y_offset + 38}" r="8" class="{email_class}"/>\n'
    )
    section += f'  <text x="175" y="{y_offset + 41}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{email_symbol}</text>\n'
    section += "  \n"
    section += f'  <text x="210" y="{y_offset + 42}" class="label">Data Protection Officer:</text>\n'
    section += f'  <circle cx="360" cy="{y_offset + 38}" r="8" class="{dpo_class}"/>\n'
    section += f'  <text x="360" y="{y_offset + 41}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{dpo_symbol}</text>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 59}" class="label">Contact Address:</text>\n'
    )
    section += (
        f'  <circle cx="175" cy="{y_offset + 55}" r="8" class="{address_class}"/>\n'
    )
    section += f'  <text x="175" y="{y_offset + 58}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{address_symbol}</text>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 76}" class="label">Contact Website:</text>\n'
    )
    section += (
        f'  <circle cx="175" cy="{y_offset + 72}" r="8" class="{website_class}"/>\n'
    )
    section += f'  <text x="175" y="{y_offset + 75}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{website_symbol}</text>\n'
    section += "  \n"
    section += f'  <rect x="30" y="{y_offset + 86}" width="340" height="20" fill="#e0e0e0" rx="3"/>\n'
    section += f'  <rect x="30" y="{y_offset + 86}" width="{meta_bar_width}" height="20" fill="{meta_color}" rx="3"/>\n'
    section += f'  <text x="200" y="{y_offset + 100}" text-anchor="middle" class="value" fill="#333">Overall: {meta_score:.2f}%</text>\n'

    return section, y_offset + 131


def generate_data_processing_section(
    y_offset: int,
    profiling: bool | None,
    automated_decision: bool | None,
    data_types_count: int,
    categories_display: list[str],
) -> tuple[str, int]:
    """Generate the data processing summary section. Returns (svg_string, final_y_position)."""

    profiling = not profiling if profiling is not None else None
    automated_decision = (
        not automated_decision if automated_decision is not None else None
    )

    profiling_symbol, profiling_class = get_checkmark_symbol(profiling)
    automated_symbol, automated_class = get_checkmark_symbol(automated_decision)

    section = """
  <!-- Data Processing Summary -->
"""
    section += f'  <text x="20" y="{y_offset}" class="section-title">Data Processing Summary</text>\n'
    section += f'  <line x1="20" y1="{y_offset + 5}" x2="380" y2="{y_offset + 5}" stroke="#000000" stroke-width="1"/>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 25}" class="label">No Profiling:</text>\n'
    )
    section += (
        f'  <circle cx="175" cy="{y_offset + 21}" r="8" class="{profiling_class}"/>\n'
    )
    section += f'  <text x="175" y="{y_offset + 24}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{profiling_symbol}</text>\n'
    section += "  \n"
    section += f'  <text x="210" y="{y_offset + 25}" class="label">No Automated Decision:</text>\n'
    section += (
        f'  <circle cx="360" cy="{y_offset + 21}" r="8" class="{automated_class}"/>\n'
    )
    section += f'  <text x="360" y="{y_offset + 24}" text-anchor="middle" fill="white" style="font-size: 10px; font-weight: bold;">{automated_symbol}</text>\n'
    section += "  \n"
    section += f'  <text x="30" y="{y_offset + 45}" class="label">Total Data Types Collected:</text>\n'
    section += f'  <text x="350" y="{y_offset + 45}" text-anchor="end" class="value">{data_types_count}</text>\n'
    section += "  \n"
    section += f'  <text x="30" y="{y_offset + 65}" class="small">Including: {categories_display[0]}</text>\n'

    for i in range(1, len(categories_display)):
        section += f'  <text x="30" y="{y_offset + 65 + (i * 15)}" class="small">{categories_display[i]}</text>\n'

    return section, y_offset + 88 + (len(categories_display) - 1) * 15


def generate_data_sharing_section(
    y_offset: int,
    sharing_types: list[str],
    total_sharing_types: int,
    companies: list[str],
    total_companies: int,
    descriptives: list[str],
    total_descriptives: int,
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

    # Shared Data Types
    section += (
        f'  <text x="30" y="{y_offset + 25}" class="label">Shared Data Types:</text>\n'
    )
    section += f'  <text x="350" y="{y_offset + 25}" text-anchor="end" class="value">{total_sharing_types}</text>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 42}" class="small">{sharing_types[0]}</text>\n'
    )
    for i in range(1, len(sharing_types)):
        section += f'  <text x="30" y="{y_offset + 42 + (i * 15)}" class="small">{sharing_types[i]}</text>\n'
    y_offset += (len(sharing_types) - 1) * 15
    section += "  \n"

    # Third Party Companies
    section += (
        f'  <text x="30" y="{y_offset + 62}" class="label">Third Parties:</text>\n'
    )
    section += f'  <text x="350" y="{y_offset + 62}" text-anchor="end" class="value">{total_companies} named</text>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 79}" class="small">{companies[0]}</text>\n'
    )
    for i in range(1, len(companies)):
        section += f'  <text x="30" y="{y_offset + 79 + (i * 15)}" class="small">, {companies[i]}</text>\n'
    y_offset += (len(companies) - 1) * 15
    section += "  \n"

    # Third Party Descriptives
    section += (
        f'  <text x="30" y="{y_offset + 99}" class="label">Third Party Types:</text>\n'
    )
    section += f'  <text x="350" y="{y_offset + 99}" text-anchor="end" class="value">{total_descriptives}</text>\n'
    section += "  \n"
    section += (
        f'  <text x="30" y="{y_offset + 116}" class="small">{descriptives[0]}</text>\n'
    )
    for i in range(1, len(descriptives)):
        section += f'  <text x="30" y="{y_offset + 116 + (i * 15)}" class="small">{descriptives[i]}</text>\n'
    y_offset += (len(descriptives) - 1) * 15

    return section, (y_offset + 147)


def generate_legal_basis_section(
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


def generate_footer(
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


def generate_svg_label(scores: ScoreReport, summary: SummaryReport, source: str) -> str:
    """Generate the complete SVG label from score and summary data."""

    # User rights
    rights_count, rights_total = count_user_rights(summary.user_rights)

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
    svg_parts.append(generate_transparency_section(scores.transparency))

    # Purposes
    purposes_svg, y_pos = generate_purposes_section(summary.purpose)
    svg_parts.append(purposes_svg)

    # Coverage
    coverage_svg, y_pos = generate_coverage_section(
        y_pos + 23,
        summary.security_privacy,
        rights_count,
        rights_total,
        summary.selling.merger_acquisition,
        summary.audience.children,
        scores.coverage.final_score,
    )
    svg_parts.append(coverage_svg)

    # Contact & Meta
    contact_svg, y_pos = generate_contact_meta_section(
        y_pos,
        summary.contact.phone,
        summary.contact.email,
        summary.contact.address,
        summary.contact.website,
        summary.policy.date is not None,
        summary.policy.data_protection_officer,
        scores.meta.final_score,
    )
    svg_parts.append(contact_svg)

    # Data Processing
    processing_svg, y_pos = generate_data_processing_section(
        y_pos,
        summary.processing.profiling,
        summary.processing.automated_decision,
        len(summary.data_type.data_types),
        categories_display,
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

    sharing_svg, y_pos = generate_data_sharing_section(
        y_pos,
        sharing_types,
        len(summary.sharing.sharing_types),
        companies,
        len(summary.third_party.companies),
        descriptives,
        len(summary.third_party.descriptives),
    )
    svg_parts.append(sharing_svg)

    # Legal Basis
    legal_svg, y_pos = generate_legal_basis_section(y_pos, summary.legal_basis)
    svg_parts.append(legal_svg)

    # Footer
    footer_svg, y_pos = generate_footer(
        y_pos,
        "unknown" if summary.policy.date is None else summary.policy.date,
        summary.policy.total_sentences,
        source,
    )
    svg_parts.append(footer_svg)

    # Calculate total height from final y position (add space for footer)
    total_height = y_pos

    # Insert header at the beginning
    svg_content = generate_svg_header(total_height) + "".join(svg_parts)

    return svg_content
