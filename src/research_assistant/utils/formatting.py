"""Output formatting utilities for reports and data.

This module provides functions for formatting research outputs, including
markdown, JSON, and HTML generation, as well as data visualization helpers.

Example:
    >>> from research_assistant.utils.formatting import format_report_metadata
    >>> metadata = format_report_metadata(state, config)
    >>> print(metadata)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from io import StringIO

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def format_timestamp(
    timestamp: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """Format timestamp for display.

    Args:
        timestamp: Datetime object. If None, uses current time.
        format_str: strftime format string.

    Returns:
        Formatted timestamp string.

    Example:
        >>> formatted = format_timestamp()
        >>> print(formatted)  # "2024-01-15 14:30:00"
    """
    if timestamp is None:
        timestamp = datetime.now()

    return timestamp.strftime(format_str)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration string.

    Example:
        >>> format_duration(3665)
        '1h 1m 5s'
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def format_number(number: int, use_separators: bool = True) -> str:
    """Format number with thousands separators.

    Args:
        number: Number to format.
        use_separators: Whether to use comma separators.

    Returns:
        Formatted number string.

    Example:
        >>> format_number(1234567)
        '1,234,567'
    """
    if use_separators:
        return f"{number:,}"
    return str(number)


def format_report_metadata(
    state: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    execution_time: Optional[float] = None,
) -> str:
    """Format research report metadata section.

    Args:
        state: Research state dictionary.
        config: Optional configuration dictionary.
        execution_time: Optional execution time in seconds.

    Returns:
        Formatted metadata markdown string.

    Example:
        >>> metadata = format_report_metadata(final_state, cfg)
    """
    lines = [
        "---",
        "## Report Metadata",
        "",
        f"**Topic:** {state.get('topic', 'N/A')}",
        f"**Generated:** {format_timestamp()}",
    ]

    if execution_time:
        lines.append(f"**Execution Time:** {format_duration(execution_time)}")

    # Analyst information
    analysts = state.get("analysts", [])
    if analysts:
        lines.extend([f"**Number of Analysts:** {len(analysts)}", "", "**Analysts:**"])
        for i, analyst in enumerate(analysts, 1):
            name = analyst.name if hasattr(analyst, "name") else analyst.get("name", "Unknown")
            role = analyst.role if hasattr(analyst, "role") else analyst.get("role", "Unknown")
            lines.append(f"{i}. {name} - {role}")

    # Configuration info
    if config:
        lines.extend(
            [
                "",
                "**Configuration:**",
                f"- LLM Model: {config.get('llm', {}).get('model', 'N/A')}",
                f"- Max Interview Turns: {config.get('research', {}).get('max_interview_turns', 'N/A')}",
            ]
        )

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def format_analyst_summary(analysts: List[Any]) -> str:
    """Format analyst list as markdown table.

    Args:
        analysts: List of Analyst objects or dictionaries.

    Returns:
        Markdown table string.

    Example:
        >>> summary = format_analyst_summary(state['analysts'])
    """
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


def format_metrics_report(metrics: Dict[str, Any]) -> str:
    """Format metrics as markdown report.

    Args:
        metrics: Metrics dictionary from logging system.

    Returns:
        Formatted metrics markdown string.

    Example:
        >>> from research_assistant.utils.logging import get_metrics
        >>> metrics = get_metrics()
        >>> report = format_metrics_report(metrics)
    """
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

    # Node execution details
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

    # Errors
    errors = metrics.get("errors", [])
    if errors:
        lines.extend(["### Errors", ""])
        for error in errors[:10]:  # Limit to 10 errors
            lines.append(f"- **{error.get('node', 'Unknown')}:** {error.get('error', 'N/A')}")

        if len(errors) > 10:
            lines.append(f"\n*... and {len(errors) - 10} more errors*")

    return "\n".join(lines)


def save_report(
    content: str, output_path: str, metadata: Optional[str] = None, metrics: Optional[str] = None
) -> None:
    """Save report to file with optional metadata and metrics.

    Args:
        content: Main report content.
        output_path: Path to save file.
        metadata: Optional metadata section.
        metrics: Optional metrics section.

    Example:
        >>> save_report(
        ...     final_report,
        ...     "./outputs/report.md",
        ...     metadata=metadata,
        ...     metrics=metrics_report
        ... )
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Assemble full content
    parts = []

    if metadata:
        parts.append(metadata)

    parts.append(content)

    if metrics:
        parts.extend(["", "---", "", metrics])

    full_content = "\n".join(parts)

    # Write to file
    output_file.write_text(full_content, encoding="utf-8")


def export_to_json(
    state: Dict[str, Any], output_path: str, indent: int = 2, include_metadata: bool = True
) -> None:
    """Export research state to JSON file.

    Args:
        state: Research state dictionary.
        output_path: Path to save JSON file.
        indent: JSON indentation level.
        include_metadata: Whether to include export metadata.

    Example:
        >>> export_to_json(final_state, "./outputs/report.json")
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data for JSON serialization
    export_data = {}

    if include_metadata:
        export_data["metadata"] = {
            "exported_at": datetime.now().isoformat(),
            "topic": state.get("topic"),
            "num_analysts": len(state.get("analysts", [])),
        }

    # Convert analysts to dicts
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

    # Add other state fields
    for key in ["topic", "sections", "introduction", "content", "conclusion", "final_report"]:
        if key in state:
            export_data[key] = state[key]

    # Write JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=indent, ensure_ascii=False)


def export_to_html(
    content: str, output_path: str, title: Optional[str] = None, css: Optional[str] = None
) -> None:
    """Export markdown content to HTML file.

    Args:
        content: Markdown content to convert.
        output_path: Path to save HTML file.
        title: Optional HTML title.
        css: Optional CSS stylesheet content.

    Example:
        >>> export_to_html(final_report, "./outputs/report.html")
    """
    try:
        import markdown
    except ImportError:
        raise ImportError(
            "markdown package required for HTML export. Install with: pip install markdown"
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert markdown to HTML
    html_content = markdown.markdown(content, extensions=["extra", "codehilite", "toc"])

    # Default CSS
    default_css = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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

    # Build full HTML
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or 'Research Report'}</title>
    <style>
        {css or default_css}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

    # Write HTML
    output_file.write_text(html_template, encoding="utf-8")


def create_filename(
    topic: str,
    template: str = "research_{topic}_{timestamp}",
    extension: str = "md",
    timestamp_format: str = "%Y%m%d_%H%M%S",
) -> str:
    """Create filename from template.

    Args:
        topic: Research topic.
        template: Filename template with placeholders.
        extension: File extension.
        timestamp_format: strftime format for timestamp.

    Returns:
        Generated filename.

    Example:
        >>> filename = create_filename("AI Safety")
        'research_ai_safety_20240115_143000.md'
    """
    # Sanitize topic for filename
    safe_topic = topic.lower().replace(" ", "_")
    safe_topic = "".join(c for c in safe_topic if c.isalnum() or c == "_")

    # Generate timestamp
    timestamp = datetime.now().strftime(timestamp_format)

    # Format filename
    filename = template.format(topic=safe_topic, timestamp=timestamp)

    return f"{filename}.{extension}"


def format_progress_bar(
    current: int, total: int, width: int = 50, prefix: str = "", suffix: str = ""
) -> str:
    """Format a text-based progress bar.

    Args:
        current: Current progress value.
        total: Total/maximum value.
        width: Width of progress bar in characters.
        prefix: Text before the bar.
        suffix: Text after the bar.

    Returns:
        Formatted progress bar string.

    Example:
        >>> bar = format_progress_bar(3, 5, prefix="Interviews")
        >>> print(bar)
        Interviews |██████████░░░░░░░░░░| 60% (3/5)
    """
    if total == 0:
        percent = 0
    else:
        percent = int((current / total) * 100)

    filled = int((current / total) * width) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)

    return f"{prefix} |{bar}| {percent}% ({current}/{total}) {suffix}".strip()


def format_table(headers: List[str], rows: List[List[Any]], markdown: bool = True) -> str:
    """Format data as a table.

    Args:
        headers: Column headers.
        rows: List of row data.
        markdown: Whether to use markdown format (vs. plain text).

    Returns:
        Formatted table string.

    Example:
        >>> table = format_table(
        ...     ["Name", "Score"],
        ...     [["Alice", 95], ["Bob", 87]]
        ... )
    """
    if not rows:
        return "No data available."

    if markdown:
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Build table
        lines = []

        # Header
        header_line = (
            "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        )
        lines.append(header_line)

        # Separator
        sep_line = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
        lines.append(sep_line)

        # Rows
        for row in rows:
            row_line = (
                "| "
                + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
                + " |"
            )
            lines.append(row_line)

        return "\n".join(lines)

    else:
        # Plain text table
        if PANDAS_AVAILABLE:
            df = pd.DataFrame(rows, columns=headers)
            return df.to_string(index=False)
        else:
            # Simple plain text format
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

            lines = []

            # Header
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            lines.append(header_line)
            lines.append("-" * len(header_line))

            # Rows
            for row in rows:
                row_line = " ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
                lines.append(row_line)

            return "\n".join(lines)


def format_list(items: List[str], ordered: bool = False, indent: int = 0) -> str:
    """Format list as markdown.

    Args:
        items: List items.
        ordered: Whether to use numbered list.
        indent: Indentation level.

    Returns:
        Formatted list string.

    Example:
        >>> formatted = format_list(["Item 1", "Item 2"], ordered=True)
    """
    lines = []
    indent_str = "  " * indent

    for i, item in enumerate(items, 1):
        if ordered:
            lines.append(f"{indent_str}{i}. {item}")
        else:
            lines.append(f"{indent_str}- {item}")

    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text.

    Example:
        >>> truncate_text("Long text here", max_length=10)
        'Long te...'
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_citation_list(citations: List[str]) -> str:
    """Format list of citations as markdown.

    Args:
        citations: List of citation strings.

    Returns:
        Formatted citations markdown.

    Example:
        >>> citations = ["Source 1", "Source 2"]
        >>> formatted = format_citation_list(citations)
    """
    if not citations:
        return "No sources cited."

    lines = ["## Sources", ""]

    for i, citation in enumerate(citations, 1):
        lines.append(f"[{i}] {citation}")

    return "\n".join(lines)


def colorize_text(text: str, color: str) -> str:
    """Add ANSI color codes to text for terminal output.

    Args:
        text: Text to colorize.
        color: Color name (red, green, blue, yellow, cyan, magenta).

    Returns:
        Text with ANSI color codes.

    Example:
        >>> colored = colorize_text("Success", "green")
        >>> print(colored)  # Prints in green if terminal supports it
    """
    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m",
    }

    color_code = colors.get(color.lower(), "")
    reset_code = colors["reset"]

    return f"{color_code}{text}{reset_code}"


def format_key_value_pairs(data: Dict[str, Any], indent: int = 0, separator: str = ": ") -> str:
    """Format dictionary as key-value pairs.

    Args:
        data: Dictionary to format.
        indent: Indentation level.
        separator: Separator between key and value.

    Returns:
        Formatted string.

    Example:
        >>> formatted = format_key_value_pairs({"name": "Alice", "age": 30})
    """
    indent_str = "  " * indent
    lines = []

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_key_value_pairs(value, indent + 1, separator))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(format_key_value_pairs(item, indent + 1, separator))
                else:
                    lines.append(f"{indent_str}  - {item}")
        else:
            lines.append(f"{indent_str}{key}{separator}{value}")

    return "\n".join(lines)


def format_error_report(errors: List[Dict[str, Any]]) -> str:
    """Format list of errors as readable report.

    Args:
        errors: List of error dictionaries with 'node', 'error', 'timestamp'.

    Returns:
        Formatted error report.

    Example:
        >>> errors = [{"node": "search", "error": "Timeout", "timestamp": "..."}]
        >>> report = format_error_report(errors)
    """
    if not errors:
        return "No errors occurred."

    lines = ["## Error Report", "", f"Total Errors: {len(errors)}", ""]

    for i, error in enumerate(errors, 1):
        lines.extend(
            [
                f"### Error {i}",
                f"- **Node:** {error.get('node', 'Unknown')}",
                f"- **Error:** {error.get('error', 'Unknown')}",
                f"- **Timestamp:** {error.get('timestamp', 'Unknown')}",
                "",
            ]
        )

    return "\n".join(lines)


# Utility for sanitizing output


def sanitize_for_filename(text: str, max_length: int = 50) -> str:
    """Sanitize text for use in filenames.

    Args:
        text: Text to sanitize.
        max_length: Maximum length of result.

    Returns:
        Sanitized text safe for filenames.

    Example:
        >>> safe = sanitize_for_filename("My Research: AI & ML")
        'my_research_ai_ml'
    """
    # Convert to lowercase
    text = text.lower()

    # Replace spaces and special chars with underscore
    text = "".join(c if c.isalnum() else "_" for c in text)

    # Remove consecutive underscores
    while "__" in text:
        text = text.replace("__", "_")

    # Trim underscores from ends
    text = text.strip("_")

    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length].rstrip("_")

    return text


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted size string.

    Example:
        >>> format_file_size(1536)
        '1.5 KB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"
