"""Utility modules for research assistant.

This package provides logging, formatting, and other utility functions.

Example:
    >>> from research_assistant.utils import setup_logging, get_logger
    >>> setup_logging(level="INFO")
    >>> logger = get_logger(__name__)
"""

from .logging import (
    setup_logging,
    setup_structlog,
    get_logger,
    log_execution,
    log_operation,
    log_function_call,
    log_performance,
    get_metrics,
    reset_metrics,
    log_metrics_summary,
    configure_from_config,
    ExecutionMetrics,
)

from .formatting import (
    format_timestamp,
    format_duration,
    format_number,
    format_report_metadata,
    format_analyst_summary,
    format_metrics_report,
    save_report,
    export_to_json,
    export_to_html,
    create_filename,
    format_progress_bar,
    format_table,
    format_list,
    truncate_text,
    format_citation_list,
    colorize_text,
    format_key_value_pairs,
    format_error_report,
    sanitize_for_filename,
    format_file_size,
)

__all__ = [
    # Logging
    "setup_logging",
    "setup_structlog",
    "get_logger",
    "log_execution",
    "log_operation",
    "log_function_call",
    "log_performance",
    "get_metrics",
    "reset_metrics",
    "log_metrics_summary",
    "configure_from_config",
    "ExecutionMetrics",
    
    # Formatting
    "format_timestamp",
    "format_duration",
    "format_number",
    "format_report_metadata",
    "format_analyst_summary",
    "format_metrics_report",
    "save_report",
    "export_to_json",
    "export_to_html",
    "create_filename",
    "format_progress_bar",
    "format_table",
    "format_list",
    "truncate_text",
    "format_citation_list",
    "colorize_text",
    "format_key_value_pairs",
    "format_error_report",
    "sanitize_for_filename",
    "format_file_size",
]
