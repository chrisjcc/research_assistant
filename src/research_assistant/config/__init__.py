"""Configuration management for research assistant.

This module provides Hydra-based configuration management with YAML files
for different components, experiments, and use cases.

Example:
    >>> from research_assistant.config import load_config, get_llm_config
    >>> cfg = load_config()
    >>> llm_config = get_llm_config(cfg)
    >>> print(llm_config['model'])
"""

from .config import (
    ConfigPaths,
    check_required_env_vars,
    create_development_config,
    create_production_config,
    create_quick_research_config,
    get_llm_config,
    get_logging_config,
    get_output_config,
    get_research_config,
    get_search_config,
    load_config,
    load_config_from_file,
    load_env_file,
    merge_configs,
    print_config,
    save_config,
    validate_config,
)

__all__ = [
    # Core loading functions
    "load_config",
    "load_config_from_file",
    "save_config",
    "merge_configs",
    # Component-specific extractors
    "get_llm_config",
    "get_search_config",
    "get_research_config",
    "get_logging_config",
    "get_output_config",
    # Validation and utilities
    "validate_config",
    "print_config",
    "load_env_file",
    "check_required_env_vars",
    # Templates
    "create_quick_research_config",
    "create_development_config",
    "create_production_config",
    # Classes
    "ConfigPaths",
]
