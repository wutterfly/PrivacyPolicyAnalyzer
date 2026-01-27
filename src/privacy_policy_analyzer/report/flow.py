from collections import defaultdict
from io import BytesIO

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from privacy_policy_analyzer.analysis.structure import StructuredEntry
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)

TOPIC_COLOR_MAP = {
    "Audience": "#e41a1c",  # Red
    "Contact": "#377eb8",  # Blue
    "Control": "#4daf4a",  # Green
    "Deletion": "#984ea3",  # Purple
    "LegalBasis": "#ff7f00",  # Orange
    "Policy": "#a65628",  # Brown
    "Processing": "#f781bf",  # Pink
    "Purpose": "#00CED1",  # Dark Turquoise
    "Retention": "#32CD32",  # Lime Green
    "Selling": "#FF1493",  # Deep Pink
    "Sharing": "#FF8C00",  # Dark Orange
    "ThirdParty": "#8B008B",  # Dark Magenta
    "UserRights": "#00FF7F",  # Spring Green
    "Security/Privacy": "#DC143C",  # Crimson
}


def generate_topic_map(data: list[StructuredEntry], dpi: int = 300) -> bytes:
    """Generate a topic map visualization from structured entries."""

    # Filter to only items with text
    data = [item for item in data if item.text.strip()]

    # Get all unique topics (excluding 'Other')
    topic_counts = defaultdict(int)
    for item in data:
        for topic in item.topics:
            if topic.topic != "Other":
                topic_counts[topic.topic] += 1

    # Keep only topics that appear at least 10 times (reduce clutter)
    significant_topics = {topic for topic, count in topic_counts.items() if count >= 5}
    all_topics = sorted(list(significant_topics))

    # Map topics to colors
    topic_colors = {}
    fallback_colors = ["#999999", "#666666", "#CCCCCC", "#555555"]
    fallback_idx = 0

    for topic in all_topics:
        if topic in TOPIC_COLOR_MAP:
            topic_colors[topic] = TOPIC_COLOR_MAP[topic]
        else:
            # Unknown topic - use fallback color
            topic_colors[topic] = fallback_colors[fallback_idx % len(fallback_colors)]
            fallback_idx += 1
            logger.warning("Unknown topic using fallback color: topic=%s", topic)

    # Create the visualization - thinner width
    fig, ax = plt.subplots(figsize=(8, 12))

    # Group items into chunks for better readability
    chunk_size = 5  # Each bar represents X items
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        # Count topics in this chunk
        chunk_topics = defaultdict(int)
        for item in chunk:
            item_topics = [
                t.topic for t in item.topics if t.topic in significant_topics
            ]
            for topic in item_topics:
                chunk_topics[topic] += 1
        chunks.append(chunk_topics)

    # Draw chunked bars
    y_position = len(chunks)
    bar_height = 1

    for chunk_topics in chunks:
        if chunk_topics:
            total = sum(chunk_topics.values())
            x_offset = 0
            for topic in all_topics:
                count = chunk_topics.get(topic, 0)
                if count > 0:
                    width = count / total
                    color = topic_colors[topic]
                    ax.barh(
                        y_position,
                        width,
                        left=x_offset,
                        height=bar_height,
                        color=color,
                        edgecolor="white",
                        linewidth=0.5,
                    )
                    x_offset += width
        else:
            ax.barh(
                y_position,
                1.0,
                height=bar_height,
                color="#f0f0f0",
                edgecolor="white",
                linewidth=0.5,
            )

        y_position -= bar_height

    # Create legend with counts - place below the chart in 4 columns
    legend_patches = [
        mpatches.Patch(
            color=topic_colors[topic], label=f"{topic} ({topic_counts[topic]})"
        )
        for topic in all_topics
    ]
    ax.legend(
        handles=legend_patches,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fontsize=9,
        frameon=True,
        ncol=4,
        title="Topics (count)",
        title_fontsize=10,
    )

    # Styling
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(chunks))
    ax.set_xlabel("Topic Distribution", fontsize=12, fontweight="bold")
    ax.set_ylabel("Position in Policy", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Privacy Policy Topic Distribution\n(Each bar = ~({chunk_size}) items)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xticks([])

    # Add position markers
    positions = [
        0,
        len(chunks) // 4,
        len(chunks) // 2,
        3 * len(chunks) // 4,
        len(chunks),
    ]
    labels = ["End", "75%", "50%", "25%", "Start"]
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=10)

    # Add subtle grid
    ax.grid(axis="y", alpha=0.2, linestyle="--")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)

    plt.close(fig)

    return buf.getvalue()


CONTEXT_COLOR_MAP = {
    "Website": "#1f77b4",  # Blue
    "App": "#ff7f0e",  # Orange
    "Device": "#2ca02c",  # Green
    "Store": "#d62728",  # Red
    "BackendService": "#9467bd",  # Purple
    "Recruitment": "#8c564b",  # Brown
    "Communication": "#e377c2",  # Pink
    "Account": "#7f7f7f",  # Gray
    "Services": "#bcbd22",  # Yellow-green
    "Event/Program": "#17becf",  # Cyan
    "Other": "#aec7e8",  # Light blue
}


def generate_context_map(data: list[StructuredEntry], dpi: int = 300) -> bytes:
    """Generate a context map visualization from structured entries."""

    # Filter to only items with text
    data = [item for item in data if item.text.strip()]

    # Get all unique contexts (excluding 'Other')
    context_counts = defaultdict(int)
    for item in data:
        for context in item.contexts:
            if context != "Other":
                context_counts[context] += 1

    # Keep only contexts that appear at least 5 times (reduce clutter)
    significant_contexts = {
        context for context, count in context_counts.items() if count >= 5
    }
    all_contexts = sorted(list(significant_contexts))

    # Map contexts to colors
    context_colors = {}
    fallback_colors = ["#999999", "#666666", "#CCCCCC", "#555555"]
    fallback_idx = 0

    for context in all_contexts:
        if context in CONTEXT_COLOR_MAP:
            context_colors[context] = CONTEXT_COLOR_MAP[context]
        else:
            # Unknown context - use fallback color
            context_colors[context] = fallback_colors[
                fallback_idx % len(fallback_colors)
            ]
            fallback_idx += 1
            logger.warning("Unknown context using fallback color: context=%s", context)

    # Create the visualization - thinner width
    fig, ax = plt.subplots(figsize=(8, 12))

    # Group items into chunks for better readability
    chunk_size = 5  # Each bar represents X items
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        # Count contexts in this chunk
        chunk_contexts = defaultdict(int)
        for item in chunk:
            item_contexts = [c for c in item.contexts if c in significant_contexts]
            for context in item_contexts:
                chunk_contexts[context] += 1
        chunks.append(chunk_contexts)

    # Draw chunked bars
    y_position = len(chunks)
    bar_height = 1

    for chunk_contexts in chunks:
        if chunk_contexts:
            total = sum(chunk_contexts.values())
            x_offset = 0
            for context in all_contexts:
                count = chunk_contexts.get(context, 0)
                if count > 0:
                    width = count / total
                    color = context_colors[context]
                    ax.barh(
                        y_position,
                        width,
                        left=x_offset,
                        height=bar_height,
                        color=color,
                        edgecolor="white",
                        linewidth=0.5,
                    )
                    x_offset += width
        else:
            ax.barh(
                y_position,
                1.0,
                height=bar_height,
                color="#f0f0f0",
                edgecolor="white",
                linewidth=0.5,
            )

        y_position -= bar_height

    # Create legend with counts - place below the chart in 4 columns
    legend_patches = [
        mpatches.Patch(
            color=context_colors[context],
            label=f"{context} ({context_counts[context]})",
        )
        for context in all_contexts
    ]
    ax.legend(
        handles=legend_patches,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fontsize=9,
        frameon=True,
        ncol=4,
        title="Contexts (count)",
        title_fontsize=10,
    )

    # Styling
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(chunks))
    ax.set_xlabel("Context Distribution", fontsize=12, fontweight="bold")
    ax.set_ylabel("Position in Policy", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Privacy Policy Context Distribution\n(Each bar = ~({chunk_size}) items)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xticks([])

    # Add position markers
    positions = [
        0,
        len(chunks) // 4,
        len(chunks) // 2,
        3 * len(chunks) // 4,
        len(chunks),
    ]
    labels = ["End", "75%", "50%", "25%", "Start"]
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=10)

    # Add subtle grid
    ax.grid(axis="y", alpha=0.2, linestyle="--")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)

    plt.close(fig)

    return buf.getvalue()
