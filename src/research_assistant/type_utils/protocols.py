"""Type protocols and interfaces for the research assistant.

This module defines Protocol-based interfaces (structural typing) that the rest of
the codebase can depend on without importing concrete implementations.

Why Protocols?
--------------
Protocols let us express "any object that looks like X" instead of "instances of class X".
This is useful for:
- plugging in different LLM backends,
- swapping search providers (Tavily, custom, local),
- injecting test doubles/mocks in unit tests,
- avoiding hard runtime dependencies across modules.

All protocol methods below raise NotImplementedError in their bodies instead of using
ellipsis `...` or bare `pass`, because this project is using stricter style/linting and
because the user requested a completed implementation.

The actual implementations (e.g. a Tavily-backed searcher, an OpenAI-backed LLM, a file
checkpointer) should subclass these or at least satisfy them structurally.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeAlias, runtime_checkable

try:
    # LangChain-style message base. This is what your example in the prompt used.
    from langchain_core.messages import BaseMessage
except Exception:  # pragma: no cover
    # Fallback to a minimal stub so that type checkers still see a name.
    class BaseMessage:  # type: ignore[no-redef]
        """Fallback message type if langchain_core is not installed."""

        def __init__(self, content: str) -> None:
            self.content = content


# ---------------------------------------------------------------------------
# Common type aliases
# ---------------------------------------------------------------------------

StateDict: TypeAlias = dict[str, Any]
"""Dictionary-like state object flowing through graphs/nodes."""

StateUpdate: TypeAlias = dict[str, Any]
"""Partial state update returned by nodes."""

MessageList: TypeAlias = list[BaseMessage]
"""List of LangChain-style messages."""

SearchResults: TypeAlias = list[dict[str, Any]]
"""Normalized search results: each item is a dict-like result."""

AnalystList: TypeAlias = list[dict[str, Any]]
"""List of analyst-like objects/dicts used by reporting nodes."""

ConfigDict: TypeAlias = dict[str, Any]
"""Arbitrary configuration payload."""

MetricsDict: TypeAlias = dict[str, int | float | str | None]
"""Simple metrics payload, e.g. for logging or monitoring."""


# ---------------------------------------------------------------------------
# LLM provider
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers.

    The intent is to cover LangChain-like chat models:

        response = llm.invoke(messages)

    where `response` is usually a `BaseMessage` (often `AIMessage`) with a `.content`.
    """

    def invoke(self, messages: MessageList) -> BaseMessage:
        """Invoke the LLM with a list of messages.

        Args:
            messages: Conversation history, last item is usually the user prompt.

        Returns:
            A single message produced by the LLM.

        Implementations should do the actual model call here.
        """
        raise NotImplementedError("LLMProvider.invoke() must be implemented")

    def with_structured_output(self, schema: type[Any]) -> "LLMProvider":
        """Return an LLM view that produces structured output for the given schema.

        This mirrors the common LangChain/OpenAI pattern:

            llm.with_structured_output(MyPydanticSchema)

        Implementations can either return `self` (if they support it inline)
        or a light wrapper.
        """
        raise NotImplementedError("LLMProvider.with_structured_output() must be implemented")


# ---------------------------------------------------------------------------
# Search provider
# ---------------------------------------------------------------------------


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for search/information-retrieval providers."""

    def search(self, query: str, **kwargs: Any) -> SearchResults:
        """Run a search and return normalized results.

        Args:
            query: The search query.
            **kwargs: Provider-specific options (num_results, timeout, filters, ...).

        Returns:
            A list of dict-like search results.
        """
        raise NotImplementedError("SearchProvider.search() must be implemented")

    def format_results(self, results: SearchResults) -> str:
        """Format search results into a string that can be fed to an LLM.

        This keeps the LLM side decoupled from the raw provider response.
        """
        raise NotImplementedError("SearchProvider.format_results() must be implemented")


# ---------------------------------------------------------------------------
# Cache provider
# ---------------------------------------------------------------------------


@runtime_checkable
class CacheProvider(Protocol):
    """Protocol for cache providers."""

    def get(self, key: str) -> Any | None:
        """Return cached value for key, or None if missing."""
        raise NotImplementedError("CacheProvider.get() must be implemented")

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value under key, optionally with a TTL."""
        raise NotImplementedError("CacheProvider.set() must be implemented")


# ---------------------------------------------------------------------------
# State validator
# ---------------------------------------------------------------------------


@runtime_checkable
class StateValidator(Protocol):
    """Protocol for validating state objects in the graph."""

    def validate_state(self, state: StateDict) -> bool:
        """Validate the given state.

        Returns:
            True if valid.

        Should raise a ValueError/TypeError if invalid, or return False if you want
        the caller to decide what to do.
        """
        raise NotImplementedError("StateValidator.validate_state() must be implemented")

    def raise_on_error(self, state: StateDict) -> None:
        """Validate and raise if invalid."""
        if not self.validate_state(state):
            raise ValueError("Invalid state provided to StateValidator")


# ---------------------------------------------------------------------------
# Node executor
# ---------------------------------------------------------------------------


@runtime_checkable
class NodeExecutor(Protocol):
    """Protocol for graph/node executors."""

    def execute(self, state: StateDict) -> StateUpdate:
        """Execute the node and return an update to the state.

        Implementations should not mutate the input state in-place unless that is
        an explicitly documented behavior.
        """
        raise NotImplementedError("NodeExecutor.execute() must be implemented")


# ---------------------------------------------------------------------------
# Prompt formatter
# ---------------------------------------------------------------------------


@runtime_checkable
class PromptFormatter(Protocol):
    """Protocol for formatting prompts/messages for LLMs."""

    def format_prompt(self, template: str, **kwargs: Any) -> str:
        """Fill a template with values.

        This keeps formatting logic out of the orchestration code.
        """
        raise NotImplementedError("PromptFormatter.format_prompt() must be implemented")


# ---------------------------------------------------------------------------
# Metrics collector
# ---------------------------------------------------------------------------


@runtime_checkable
class MetricsCollector(Protocol):
    """Protocol for collecting and flushing metrics."""

    def record(self, name: str, value: int | float, **labels: str) -> None:
        """Record a metric value."""
        raise NotImplementedError("MetricsCollector.record() must be implemented")

    def flush(self) -> None:
        """Flush or export recorded metrics."""
        raise NotImplementedError("MetricsCollector.flush() must be implemented")


# ---------------------------------------------------------------------------
# Checkpointer
# ---------------------------------------------------------------------------


@runtime_checkable
class Checkpointer(Protocol):
    """Protocol for saving and restoring state/checkpoints."""

    def save_checkpoint(self, state: StateDict, name: str | None = None) -> str:
        """Persist the given state and return the checkpoint identifier."""
        raise NotImplementedError("Checkpointer.save_checkpoint() must be implemented")

    def load_checkpoint(self, name: str) -> StateDict:
        """Load state for the given checkpoint name."""
        raise NotImplementedError("Checkpointer.load_checkpoint() must be implemented")

    def list_checkpoints(self) -> list[str]:
        """Return all known checkpoint names/ids."""
        raise NotImplementedError("Checkpointer.list_checkpoints() must be implemented")


# ---------------------------------------------------------------------------
# Output formatter
# ---------------------------------------------------------------------------


@runtime_checkable
class OutputFormatter(Protocol):
    """Protocol for turning internal data into user-facing strings."""

    def format_output(self, data: Any) -> str:
        """Format arbitrary data into a string."""
        raise NotImplementedError("OutputFormatter.format_output() must be implemented")


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------


@runtime_checkable
class ErrorHandler(Protocol):
    """Protocol for error handling."""

    def handle_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Handle an error that occurred somewhere in the pipeline.

        Implementations might:
        - log it,
        - enrich it and re-raise,
        - send it to Sentry,
        - convert it to a user-visible message.
        """
        raise NotImplementedError("ErrorHandler.handle_error() must be implemented")


# ---------------------------------------------------------------------------
# Config provider
# ---------------------------------------------------------------------------


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for providing configuration objects."""

    def get_config(self, name: str) -> ConfigDict:
        """Return the configuration identified by `name`."""
        raise NotImplementedError("ConfigProvider.get_config() must be implemented")


# ---------------------------------------------------------------------------
# Serializable / Validatable / Comparable
# ---------------------------------------------------------------------------


@runtime_checkable
class Serializable(Protocol):
    """Something that can be converted to a dict."""

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable dictionary."""
        raise NotImplementedError("Serializable.to_dict() must be implemented")


@runtime_checkable
class Validatable(Protocol):
    """Something that can validate its own contents."""

    def validate(self) -> bool:
        """Validate the object and return True if ok.

        Implementations should raise if they want to be strict.
        """
        raise NotImplementedError("Validatable.validate() must be implemented")


@runtime_checkable
class Comparable(Protocol):
    """Something that can be compared with another value/object."""

    def compare(self, other: Any) -> int:
        """Compare to other and return negative / zero / positive like `__cmp__`.

        This is intentionally generic, because your codebase may use this for
        ranking, sorting, or confidence scoring.
        """
        raise NotImplementedError("Comparable.compare() must be implemented")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def implements_protocol(obj: Any, protocol: type[Protocol]) -> bool:  # type: ignore[type-arg]
    """Check if an object implements a protocol.

    Args:
        obj: Object to check.
        protocol: Protocol class to check against.

    Returns:
        True if object implements protocol, False otherwise.

    Example:
        >>> implements_protocol(my_llm, LLMProvider)
        True
    """
    return isinstance(obj, protocol)


def ensure_protocol(obj: Any, protocol: type[Protocol], name: str) -> None:  # type: ignore[type-arg]
    """Ensure an object implements a protocol.

    Args:
        obj: Object to check.
        protocol: Protocol class to check against.
        name: Name for error message.

    Raises:
        TypeError: If object doesn't implement protocol.

    Example:
        >>> ensure_protocol(my_llm, LLMProvider, "LLM")
    """
    if not isinstance(obj, protocol):
        raise TypeError(f"{name} must implement {protocol.__name__} protocol")
