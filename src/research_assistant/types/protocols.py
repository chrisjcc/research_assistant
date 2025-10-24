"""Type protocols and interfaces for research assistant.

This module defines Protocol classes for structural subtyping (duck typing with
type safety) and common interfaces used throughout the application.

Example:
    >>> from research_assistant.types.protocols import LLMProvider
    >>> 
    >>> class MyLLM:
    ...     def invoke(self, messages: list) -> str:
    ...         return "response"
    >>> 
    >>> # MyLLM satisfies LLMProvider protocol
    >>> llm: LLMProvider = MyLLM()
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from langchain_core.messages import BaseMessage


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers.
    
    Any class that implements these methods can be used as an LLM provider.
    """
    
    def invoke(self, messages: List[BaseMessage]) -> Any:
        """Invoke the LLM with messages.
        
        Args:
            messages: List of messages to send to LLM.
            
        Returns:
            LLM response.
        """
        ...
    
    def with_structured_output(self, schema: type) -> "LLMProvider":
        """Configure LLM for structured output.
        
        Args:
            schema: Pydantic schema for output.
            
        Returns:
            Configured LLM instance.
        """
        ...


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for search providers."""
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Execute search query.
        
        Args:
            query: Search query string.
            
        Returns:
            List of search results.
        """
        ...
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for LLM context.
        
        Args:
            results: Search results to format.
            
        Returns:
            Formatted string.
        """
        ...


@runtime_checkable
class CacheProvider(Protocol):
    """Protocol for cache providers."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None.
        """
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        ...
    
    def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key.
        """
        ...
    
    def clear(self) -> None:
        """Clear all cached values."""
        ...


@runtime_checkable
class StateValidator(Protocol):
    """Protocol for state validators."""
    
    def validate(self, state: Dict[str, Any]) -> bool:
        """Validate state structure and content.
        
        Args:
            state: State dictionary to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        ...
    
    def get_errors(self) -> List[str]:
        """Get validation errors from last validation.
        
        Returns:
            List of error messages.
        """
        ...


@runtime_checkable
class NodeExecutor(Protocol):
    """Protocol for graph node executors."""
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node logic.
        
        Args:
            state: Current state.
            
        Returns:
            State updates.
        """
        ...


@runtime_checkable
class PromptFormatter(Protocol):
    """Protocol for prompt formatters."""
    
    def format(self, **kwargs: Any) -> str:
        """Format prompt with provided arguments.
        
        Args:
            **kwargs: Arguments for prompt formatting.
            
        Returns:
            Formatted prompt string.
        """
        ...


@runtime_checkable
class MetricsCollector(Protocol):
    """Protocol for metrics collectors."""
    
    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric.
        
        Args:
            name: Metric name.
            value: Metric value.
            tags: Optional tags for the metric.
        """
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics.
        
        Returns:
            Dictionary of metrics.
        """
        ...


@runtime_checkable
class Checkpointer(Protocol):
    """Protocol for state checkpointing."""
    
    def save(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        """Save a checkpoint.
        
        Args:
            checkpoint_id: Unique checkpoint identifier.
            state: State to save.
        """
        ...
    
    def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint identifier.
            
        Returns:
            Loaded state or None if not found.
        """
        ...
    
    def list_checkpoints(self) -> List[str]:
        """List all available checkpoints.
        
        Returns:
            List of checkpoint IDs.
        """
        ...


@runtime_checkable
class OutputFormatter(Protocol):
    """Protocol for output formatters."""
    
    def format(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Format content for output.
        
        Args:
            content: Content to format.
            metadata: Optional metadata.
            
        Returns:
            Formatted output.
        """
        ...
    
    def save(self, content: str, output_path: str) -> None:
        """Save formatted content to file.
        
        Args:
            content: Content to save.
            output_path: Path to output file.
        """
        ...


@runtime_checkable
class ErrorHandler(Protocol):
    """Protocol for error handlers."""
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Handle an error.
        
        Args:
            error: Exception to handle.
            context: Optional context information.
            
        Returns:
            Recovery value or re-raises exception.
        """
        ...
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if error should trigger retry.
        
        Args:
            error: Exception to check.
            
        Returns:
            True if should retry, False otherwise.
        """
        ...


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for configuration providers."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (can be dot-notation path).
            default: Default value if key not found.
            
        Returns:
            Configuration value.
        """
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key.
            value: Value to set.
        """
        ...
    
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if valid, False otherwise.
        """
        ...


# Type aliases for common patterns

from typing import TypeAlias

# State types
StateDict: TypeAlias = Dict[str, Any]
StateUpdate: TypeAlias = Dict[str, Any]

# Message types
MessageList: TypeAlias = List[BaseMessage]

# Result types
SearchResults: TypeAlias = List[Dict[str, Any]]
AnalystList: TypeAlias = List[Any]  # List[Analyst] but avoiding circular import

# Configuration types
ConfigDict: TypeAlias = Dict[str, Any]

# Metrics types
MetricsDict: TypeAlias = Dict[str, Any]


# Generic protocols for common patterns

@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable":
        """Create instance from dictionary.
        
        Args:
            data: Dictionary data.
            
        Returns:
            New instance.
        """
        ...


@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> bool:
        """Validate the object.
        
        Returns:
            True if valid, False otherwise.
        """
        ...
    
    def get_validation_errors(self) -> List[str]:
        """Get validation errors.
        
        Returns:
            List of error messages.
        """
        ...


@runtime_checkable
class Comparable(Protocol):
    """Protocol for comparable objects."""
    
    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        ...
    
    def __lt__(self, other: Any) -> bool:
        """Check less than."""
        ...


# Utility functions for protocol checking

def implements_protocol(obj: Any, protocol: type) -> bool:
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


def ensure_protocol(obj: Any, protocol: type, name: str = "object") -> None:
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
        raise TypeError(
            f"{name} must implement {protocol.__name__} protocol"
        )
