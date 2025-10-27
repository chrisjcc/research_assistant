"""Type definitions, protocols, and validation for research assistant.

This package provides:
- Protocol definitions for structural subtyping
- Runtime type validation utilities
- Type aliases for common patterns
- Pydantic model validation helpers

Example:
    >>> from research_assistant.type_utils import (
    ...     LLMProvider,
    ...     validate_type,
    ...     validate_function_args
    ... )
"""

# Protocols
from .protocols import (
    LLMProvider,
    SearchProvider,
    CacheProvider,
    StateValidator,
    NodeExecutor,
    PromptFormatter,
    MetricsCollector,
    Checkpointer,
    OutputFormatter,
    ErrorHandler,
    ConfigProvider,
    Serializable,
    Validatable,
    Comparable,
    implements_protocol,
    ensure_protocol,
    # Type aliases
    StateDict,
    StateUpdate,
    MessageList,
    SearchResults,
    AnalystList,
    ConfigDict,
    MetricsDict,
)

# Validation
from .validation import (
    validate_type,
    validate_function_args,
    TypeValidator,
    validate_non_empty_string,
    validate_positive_number,
    validate_range,
    validate_list_length,
    validate_dict_keys,
    validate_pydantic_model,
    validate_model_list,
    validate_input_model,
    validate_output_model,
    StringValidator,
    NumberValidator,
    ListValidator,
    ValidationResult,
    create_validator,
)

__all__ = [
    # Protocols
    "LLMProvider",
    "SearchProvider",
    "CacheProvider",
    "StateValidator",
    "NodeExecutor",
    "PromptFormatter",
    "MetricsCollector",
    "Checkpointer",
    "OutputFormatter",
    "ErrorHandler",
    "ConfigProvider",
    "Serializable",
    "Validatable",
    "Comparable",
    "implements_protocol",
    "ensure_protocol",
    # Type aliases
    "StateDict",
    "StateUpdate",
    "MessageList",
    "SearchResults",
    "AnalystList",
    "ConfigDict",
    "MetricsDict",
    # Validation
    "validate_type",
    "validate_function_args",
    "TypeValidator",
    "validate_non_empty_string",
    "validate_positive_number",
    "validate_range",
    "validate_list_length",
    "validate_dict_keys",
    "validate_pydantic_model",
    "validate_model_list",
    "validate_input_model",
    "validate_output_model",
    "StringValidator",
    "NumberValidator",
    "ListValidator",
    "ValidationResult",
    "create_validator",
]

# Version info
__version__ = "0.1.0"
