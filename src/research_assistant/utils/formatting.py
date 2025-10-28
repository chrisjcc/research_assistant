"""Output formatting utilities for reports and data.

This module provides functions for formatting research outputs, including
markdown, JSON, and HTML generation, as well as data visualization helpers.

Example:
    >>> from research_assistant.utils.formatting import format_report_metadata
    >>> metadata = format_report_metadata(state, config)
    >>> print(metadata)
"""

import json
import typing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def format_timestamp(
    timestamp: datetime | None = None, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return timestamp.strftime(format_str)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"

    if seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


def format_number(number: int, use_separators: bool = True) -> str:
    """Format number with thousands separators."""
    if use_separators:
        return f"{number:,}"
    return str(number)


def format_report_metadata(
    state: dict[str, Any],
    config: dict[str, Any] | None = None,
    execution_time: float | None = None,
) -> str:
    """Format research report metadata section."""
    lines = [
        "---",
        "## Report Metadata",
        "",
        f"**Topic:** {state.get('topic', 'N/A')}",
        f"**Generated:** {format_timestamp()}",
    ]

    if execution_time:
        lines.append(f"**Execution Time:** {format_duration(execution_time)}")

    analysts = state.get("analysts", [])
    if analysts:
        lines.extend([f"**Number of Analysts:** {len(analysts)}", "", "**Analysts:**"])
        for i, analyst in enumerate(analysts, 1):
            name = analyst.name if hasattr(analyst, "name") else analyst.get("name", "Unknown")
            role = analyst.role if hasattr(analyst, "role") else analyst.get("role", "Unknown")
            lines.append(f"{i}. {name} - {role}")

    if config:
        lines.extend(
            [
                "",
                "**Configuration:**",
                f"- Max Interview Turns: "
                f"{config.get('research', {}).get('max_interview_turns', 'N/A')}",
            ]
        )

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def format_analyst_summary(analysts: list[Any]) -> str:
    """Format analyst list as markdown table."""
    if not analysts:
        return "No analysts available."

    lines = ["| # | Name | Role | Affiliation |", "|---|------|------|-------------|"]

    for i, analyst in enumerate(analysts, 1):
        if hasattr(analyst, "name"):
            name = analyst.name
            role = analyst.role
            affiliation = analyst.affiliation
        else:
            name = analyst.get("name", "Unknown")
            role = analyst.get("role", "Unknown")
            affiliation = analyst.get("affiliation", "Unknown")

        lines.append(f"| {i} | {name} | {role} | {affiliation} |")

    return "\n".join(lines)


def format_metrics_report(metrics: dict[str, Any]) -> str:
    """Format metrics as markdown report."""
    lines = [
        "## Execution Metrics",
        "",
        "### Summary",
        f"- **Total Runtime:** {format_duration(metrics.get('total_runtime', 0))}",
        f"- **API Calls:** {format_number(metrics.get('api_calls', 0))}",
        f"- **Total Tokens:** {format_number(metrics.get('total_tokens', 0))}",
        f"- **Nodes Executed:** {len(metrics.get('node_executions', {}))}",
        f"- **Errors:** {len(metrics.get('errors', []))}",
        "",
    ]

    node_execs = metrics.get("node_executions", {})
    if node_execs:
        lines.extend(
            [
                "### Node Execution Details",
                "",
                "| Node | Executions | Avg Duration | Total Tokens |",
                "|------|------------|--------------|--------------|",
            ]
        )

        for node_name, executions in node_execs.items():
            if executions:
                count = len(executions)
                avg_dur = sum(e.get("duration", 0) for e in executions) / count
                total_tokens = sum(e.get("tokens_used", 0) for e in executions)

                lines.append(
                    f"| {node_name} | {count} | {format_duration(avg_dur)} | "
                    f"{format_number(total_tokens)} |"
                )

        lines.append("")

    errors = metrics.get("errors", [])
    if errors:
        lines.extend(["### Errors", ""])
        for error in errors[:10]:
            lines.append(f"- **{error.get('node', 'Unknown')}:** {error.get('error', 'N/A')}")
        if len(errors) > 10:
            lines.append(f"\n*... and {len(errors) - 10} more errors*")

    return "\n".join(lines)


def save_report(
    content: str, output_path: str, metadata: str | None = None, metrics: str | None = None
) -> None:
    """Save report to file with optional metadata and metrics."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    if metadata:
        parts.append(metadata)
    parts.append(content)
    if metrics:
        parts.extend(["", "---", "", metrics])

    full_content = "\n".join(parts)
    output_file.write_text(full_content, encoding="utf-8")


def export_to_json(
    state: dict[str, Any], output_path: str, indent: int = 2, include_metadata: bool = True
) -> None:
    """Export research state to JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    export_data: dict[str, Any] = {}

    if include_metadata:
        export_data["metadata"] = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "topic": state.get("topic"),
            "num_analysts": len(state.get("analysts", [])),
        }

    analysts = state.get("analysts", [])
    if analysts:
        export_data["analysts"] = [
            {
                "name": a.name if hasattr(a, "name") else a.get("name"),
                "role": a.role if hasattr(a, "role") else a.get("role"),
                "affiliation": a.affiliation if hasattr(a, "affiliation") else a.get("affiliation"),
                "description": a.description if hasattr(a, "description") else a.get("description"),
            }
            for a in analysts
        ]

    for key in ["topic", "sections", "introduction", "content", "conclusion", "final_report"]:
        if key in state:
            export_data[key] = state[key]

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=indent, ensure_ascii=False)


def export_to_html(
    content: str, output_path: str, title: str | None = None, css: str | None = None
) -> None:
    """Export markdown content to HTML file."""
    try:
        import markdown  # type: ignore
    except ImportError as e:
        raise ImportError(
            "markdown package required for HTML export. Install with: pip install markdown"
        ) from e

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    html_content = markdown.markdown(content, extensions=["extra", "codehilite", "toc"])

    default_css = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
        'Helvetica Neue', Arial, sans-serif;
        line-height: 1.6;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        color: #333;
    }
    h1, h2, h3 { color: #2c3e50; }
    h1 { border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; margin-top: 30px; }
    code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
    pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
    blockquote { border-left: 4px solid #3498db; margin: 0; padding-left: 20px; color: #666; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f4f4f4; }
    a { color: #3498db; text-decoration: none; }
    a:hover { text-decoration: underline; }
    """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or 'Research Report'}</title>
    <style>{css or default_css}</style>
</head>
<body>
    {html_content}
</body>
</html>"""

    output_file.write_text(html_template, encoding="utf-8")


def create_filename(
    topic: str,
    template: str = "research_{topic}_{timestamp}",
    extension: str = "md",
    timestamp_format: str = "%Y%m%d_%H%M%S",
) -> str:
    """Create filename from template."""
    safe_topic = topic.lower().replace(" ", "_")
    safe_topic = "".join(c for c in safe_topic if c.isalnum() or c == "_")
    timestamp = datetime.now(timezone.utc).strftime(timestamp_format)
    filename = template.format(topic=safe_topic, timestamp=timestamp)
    return f"{filename}.{extension}"


def format_progress_bar(
    current: int, total: int, width: int = 50, prefix: str = "", suffix: str = ""
) -> str:
    """Format a text-based progress bar."""
    percent = 0 if total == 0 else int(current / total * 100)
    filled: int = int((current / total) * width) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    return f"{prefix} |{bar}| {percent}% ({current}/{total}) {suffix}".strip()


def format_file_size(size_bytes: float | int) -> str:
    """Format file size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
