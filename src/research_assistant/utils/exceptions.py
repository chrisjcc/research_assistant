"""Custom exception classes for research assistant.

This module defines a hierarchy of custom exceptions for better error handling
and debugging throughout the application.

Example:
    >>> from research_assistant.utils.exceptions import AnalystCreationError
    >>> raise AnalystCreationError("Failed to generate analysts", recoverable=True)
"""

from typing import Any


class ResearchAssistantError(Exception):
    """Base exception for all research assistant errors.

    All custom exceptions should inherit from this class.

    Attributes:
        message: Error message.
        details: Additional error details.
        recoverable: Whether the error is recoverable.
        context: Context information when error occurred.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        recoverable: bool = False,
        context: dict[str, Any] | None = None,
    ):
        """Initialize exception.

        Args:
            message: Human-readable error message.
            details: Additional error details.
            recoverable: Whether the operation can be retried.
            context: Context when error occurred.
        """
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.context = context or {}

        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        return " | ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary.

        Returns:
            Dictionary representation of the exception.
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "context": self.context,
        }


# Configuration Errors


class ConfigurationError(ResearchAssistantError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details=details, recoverable=False, **kwargs)


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing."""

    def __init__(self, service: str, env_var: str, **kwargs):
        message = f"Missing API key for {service}. Set {env_var} environment variable."
        details = {"service": service, "env_var": env_var}
        super().__init__(message, details=details, **kwargs)


# Analyst Errors


class AnalystError(ResearchAssistantError):
    """Base class for analyst-related errors."""

    pass


class AnalystCreationError(AnalystError):
    """Raised when analyst creation fails."""

    def __init__(self, message: str, topic: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if topic:
            details["topic"] = topic
        super().__init__(message, details=details, recoverable=True, **kwargs)


class AnalystValidationError(AnalystError):
    """Raised when analyst validation fails."""

    def __init__(self, message: str, analyst_name: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if analyst_name:
            details["analyst_name"] = analyst_name
        super().__init__(message, details=details, recoverable=False, **kwargs)


class InsufficientAnalystsError(AnalystError):
    """Raised when not enough analysts are generated."""

    def __init__(self, expected: int, actual: int, **kwargs):
        message = f"Expected {expected} analysts, but only {actual} were generated"
        details = {"expected": expected, "actual": actual}
        super().__init__(message, details=details, recoverable=True, **kwargs)


# Interview Errors


class InterviewError(ResearchAssistantError):
    """Base class for interview-related errors."""

    pass


class QuestionGenerationError(InterviewError):
    """Raised when question generation fails."""

    def __init__(self, message: str, analyst: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if analyst:
            details["analyst"] = analyst
        super().__init__(message, details=details, recoverable=True, **kwargs)


class AnswerGenerationError(InterviewError):
    """Raised when answer generation fails."""

    def __init__(self, message: str, context_available: bool = False, **kwargs):
        details = kwargs.pop("details", {})
        details["context_available"] = context_available
        super().__init__(message, details=details, recoverable=True, **kwargs)


class InterviewTimeoutError(InterviewError):
    """Raised when interview exceeds time limit."""

    def __init__(self, timeout_seconds: float, **kwargs):
        message = f"Interview timed out after {timeout_seconds} seconds"
        details = {"timeout_seconds": timeout_seconds}
        super().__init__(message, details=details, recoverable=False, **kwargs)


# Search Errors


class SearchError(ResearchAssistantError):
    """Base class for search-related errors."""

    pass


class WebSearchError(SearchError):
    """Raised when web search fails."""

    def __init__(self, message: str, query: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if query:
            details["query"] = query
        super().__init__(message, details=details, recoverable=True, **kwargs)


class WikipediaSearchError(SearchError):
    """Raised when Wikipedia search fails."""

    def __init__(self, message: str, query: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if query:
            details["query"] = query
        super().__init__(message, details=details, recoverable=True, **kwargs)


class SearchTimeoutError(SearchError):
    """Raised when search times out."""

    def __init__(self, query: str, timeout_seconds: float, **kwargs):
        message = f"Search timed out after {timeout_seconds}s for query: {query}"
        details = {"query": query, "timeout_seconds": timeout_seconds}
        super().__init__(message, details=details, recoverable=True, **kwargs)


class RateLimitError(SearchError):
    """Raised when rate limit is exceeded."""

    def __init__(self, service: str, retry_after: float | None = None, **kwargs):
        message = f"Rate limit exceeded for {service}"
        details = {"service": service}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, details=details, recoverable=True, **kwargs)


class NoSearchResultsError(SearchError):
    """Raised when search returns no results."""

    def __init__(self, query: str, search_type: str = "web", **kwargs):
        message = f"No results found for {search_type} search: {query}"
        details = {"query": query, "search_type": search_type}
        super().__init__(message, details=details, recoverable=True, **kwargs)


# Report Errors


class ReportError(ResearchAssistantError):
    """Base class for report generation errors."""

    pass


class SectionGenerationError(ReportError):
    """Raised when section generation fails."""

    def __init__(self, message: str, section_type: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if section_type:
            details["section_type"] = section_type
        super().__init__(message, details=details, recoverable=True, **kwargs)


class ReportSynthesisError(ReportError):
    """Raised when report synthesis fails."""

    def __init__(self, message: str, num_sections: int | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if num_sections is not None:
            details["num_sections"] = num_sections
        super().__init__(message, details=details, recoverable=True, **kwargs)


class MissingSectionsError(ReportError):
    """Raised when required sections are missing."""

    def __init__(self, missing_sections: list, **kwargs):
        message = f"Missing required sections: {', '.join(missing_sections)}"
        details = {"missing_sections": missing_sections}
        super().__init__(message, details=details, recoverable=False, **kwargs)


class InvalidReportFormatError(ReportError):
    """Raised when report format is invalid."""

    def __init__(self, message: str, format_type: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if format_type:
            details["format_type"] = format_type
        super().__init__(message, details=details, recoverable=False, **kwargs)


# LLM Errors


class LLMError(ResearchAssistantError):
    """Base class for LLM-related errors."""

    pass


class LLMAPIError(LLMError):
    """Raised when LLM API call fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        api_error: str | None = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if status_code:
            details["status_code"] = status_code
        if api_error:
            details["api_error"] = api_error
        super().__init__(message, details=details, recoverable=True, **kwargs)


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    def __init__(self, timeout_seconds: float, **kwargs):
        message = f"LLM request timed out after {timeout_seconds}s"
        details = {"timeout_seconds": timeout_seconds}
        super().__init__(message, details=details, recoverable=True, **kwargs)


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or malformed."""

    def __init__(self, message: str, response_type: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if response_type:
            details["response_type"] = response_type
        super().__init__(message, details=details, recoverable=True, **kwargs)


class TokenLimitError(LLMError):
    """Raised when token limit is exceeded."""

    def __init__(self, tokens_used: int, token_limit: int, **kwargs):
        message = f"Token limit exceeded: {tokens_used} > {token_limit}"
        details = {"tokens_used": tokens_used, "token_limit": token_limit}
        super().__init__(message, details=details, recoverable=False, **kwargs)


# State Errors


class StateError(ResearchAssistantError):
    """Base class for state-related errors."""

    pass


class InvalidStateError(StateError):
    """Raised when state is invalid."""

    def __init__(self, message: str, state_key: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if state_key:
            details["state_key"] = state_key
        super().__init__(message, details=details, recoverable=False, **kwargs)


class MissingStateFieldError(StateError):
    """Raised when required state field is missing."""

    def __init__(self, field_name: str, node_name: str | None = None, **kwargs):
        message = f"Missing required state field: {field_name}"
        details = {"field_name": field_name}
        if node_name:
            details["node_name"] = node_name
        super().__init__(message, details=details, recoverable=False, **kwargs)


class StateValidationError(StateError):
    """Raised when state validation fails."""

    def __init__(self, message: str, validation_errors: list | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(message, details=details, recoverable=False, **kwargs)


# Graph Errors


class GraphError(ResearchAssistantError):
    """Base class for graph execution errors."""

    pass


class GraphExecutionError(GraphError):
    """Raised when graph execution fails."""

    def __init__(self, message: str, node_name: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if node_name:
            details["node_name"] = node_name
        super().__init__(message, details=details, recoverable=True, **kwargs)


class NodeExecutionError(GraphError):
    """Raised when a specific node fails."""

    def __init__(self, node_name: str, original_error: Exception | None = None, **kwargs):
        message = f"Node '{node_name}' execution failed"
        details = kwargs.pop("details", {})
        details["node_name"] = node_name
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, details=details, recoverable=True, **kwargs)


class GraphInterruptError(GraphError):
    """Raised when graph is interrupted unexpectedly."""

    def __init__(self, message: str, checkpoint_id: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if checkpoint_id:
            details["checkpoint_id"] = checkpoint_id
        super().__init__(message, details=details, recoverable=True, **kwargs)


# Data Errors


class DataError(ResearchAssistantError):
    """Base class for data-related errors."""

    pass


class DataValidationError(DataError):
    """Raised when data validation fails."""

    def __init__(self, message: str, field_name: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if field_name:
            details["field_name"] = field_name
        super().__init__(message, details=details, recoverable=False, **kwargs)


class DataTransformationError(DataError):
    """Raised when data transformation fails."""

    def __init__(self, message: str, transform_type: str | None = None, **kwargs):
        details = kwargs.pop("details", {})
        if transform_type:
            details["transform_type"] = transform_type
        super().__init__(message, details=details, recoverable=True, **kwargs)


# File/IO Errors


class FileError(ResearchAssistantError):
    """Base class for file operation errors."""

    pass


class FileReadError(FileError):
    """Raised when file cannot be read."""

    def __init__(self, filepath: str, original_error: Exception | None = None, **kwargs):
        message = f"Failed to read file: {filepath}"
        details = {"filepath": filepath}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, details=details, recoverable=False, **kwargs)


class FileWriteError(FileError):
    """Raised when file cannot be written."""

    def __init__(self, filepath: str, original_error: Exception | None = None, **kwargs):
        message = f"Failed to write file: {filepath}"
        details = {"filepath": filepath}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, details=details, recoverable=False, **kwargs)


class InvalidFileFormatError(FileError):
    """Raised when file format is invalid."""

    def __init__(self, filepath: str, expected_format: str, **kwargs):
        message = f"Invalid file format: {filepath} (expected {expected_format})"
        details = {"filepath": filepath, "expected_format": expected_format}
        super().__init__(message, details=details, recoverable=False, **kwargs)


# Utility functions for error handling


def is_recoverable_error(error: Exception) -> bool:
    """Check if an error is recoverable.

    Args:
        error: Exception to check.

    Returns:
        True if error is recoverable, False otherwise.

    Example:
        >>> try:
        ...     raise AnalystCreationError("Failed", recoverable=True)
        ... except Exception as e:
        ...     if is_recoverable_error(e):
        ...         # Retry
        ...         pass
    """
    if isinstance(error, ResearchAssistantError):
        return error.recoverable
    return False


def get_error_context(error: Exception) -> dict[str, Any]:
    """Extract context from an error.

    Args:
        error: Exception to extract context from.

    Returns:
        Dictionary with error context.

    Example:
        >>> context = get_error_context(error)
        >>> print(context['node_name'])
    """
    if isinstance(error, ResearchAssistantError):
        return error.context
    return {}


def format_error_for_logging(error: Exception) -> dict[str, Any]:
    """Format error for structured logging.

    Args:
        error: Exception to format.

    Returns:
        Dictionary suitable for logging.

    Example:
        >>> logger.error("Operation failed", extra=format_error_for_logging(e))
    """
    if isinstance(error, ResearchAssistantError):
        return error.to_dict()

    return {"error_type": type(error).__name__, "message": str(error), "recoverable": False}
