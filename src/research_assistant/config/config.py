"""Configuration management using Hydra.

This module provides utilities for loading, validating, and accessing
configuration settings throughout the application.

Example:
    >>> from research_assistant.config import load_config, get_llm_config
    >>> cfg = load_config()
    >>> llm_config = get_llm_config(cfg)
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)


@dataclass
class ConfigPaths:
    """Configuration file paths."""

    root: Path
    config_dir: Path
    default: Path
    llm_dir: Path
    search_dir: Path

    @classmethod
    def from_package(cls) -> "ConfigPaths":
        """Create ConfigPaths from package structure.

        Returns:
            ConfigPaths instance with standard paths.
        """
        # Get package root
        current_file = Path(__file__)
        root = current_file.parent.parent.parent  # Go up to project root
        config_dir = root / "config"

        return cls(
            root=root,
            config_dir=config_dir,
            default=config_dir / "default.yaml",
            llm_dir=config_dir / "llm",
            search_dir=config_dir / "search",
        )

    def validate(self) -> bool:
        """Validate that config directories exist.

        Returns:
            True if all paths exist, False otherwise.
        """
        paths_to_check = [self.config_dir, self.default, self.llm_dir, self.search_dir]

        for path in paths_to_check:
            if not path.exists():
                logger.warning(f"Config path does not exist: {path}")
                return False

        return True


def load_config(
    config_name: str = "default",
    overrides: Optional[list] = None,
    config_path: Optional[str] = None,
) -> DictConfig:
    """Load configuration using Hydra.

    Args:
        config_name: Name of the config file (without .yaml).
        overrides: List of override strings (e.g., ["llm=anthropic", "research.max_analysts=5"]).
        config_path: Optional custom config directory path.

    Returns:
        DictConfig object with loaded configuration.

    Raises:
        RuntimeError: If configuration loading fails.

    Example:
        >>> cfg = load_config()
        >>> cfg = load_config(overrides=["llm=anthropic", "research.max_analysts=5"])
    """
    logger.info(f"Loading configuration: {config_name}")

    # Clear any existing Hydra instance
    GlobalHydra.instance().clear()

    # Determine config path
    if config_path is None:
        paths = ConfigPaths.from_package()
        config_path = str(paths.config_dir.absolute())

    logger.debug(f"Config path: {config_path}")

    try:
        # Initialize Hydra with config directory
        initialize_config_dir(config_dir=config_path, version_base=None)

        # Compose configuration with overrides
        cfg = compose(config_name=config_name, overrides=overrides or [])

        logger.info("Configuration loaded successfully")
        logger.debug(f"Config keys: {list(cfg.keys())}")

        return cfg

    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}", exc_info=True)
        raise RuntimeError(f"Configuration loading failed: {str(e)}") from e


def load_config_from_file(file_path: str) -> DictConfig:
    """Load configuration from a specific YAML file.

    Args:
        file_path: Path to YAML configuration file.

    Returns:
        DictConfig object with loaded configuration.

    Example:
        >>> cfg = load_config_from_file("./my_config.yaml")
    """
    logger.info(f"Loading configuration from file: {file_path}")

    try:
        cfg = OmegaConf.load(file_path)
        logger.info("Configuration loaded from file successfully")
        return cfg
    except Exception as e:
        logger.error(f"Failed to load config from file: {str(e)}")
        raise


def save_config(cfg: DictConfig, output_path: str) -> None:
    """Save configuration to YAML file.

    Args:
        cfg: Configuration to save.
        output_path: Path to save configuration file.

    Example:
        >>> save_config(cfg, "./saved_config.yaml")
    """
    logger.info(f"Saving configuration to: {output_path}")

    try:
        # Convert to container and save
        OmegaConf.save(cfg, output_path)
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        raise


def merge_configs(base_cfg: DictConfig, override_cfg: DictConfig) -> DictConfig:
    """Merge two configurations with override taking precedence.

    Args:
        base_cfg: Base configuration.
        override_cfg: Override configuration.

    Returns:
        Merged configuration.

    Example:
        >>> merged = merge_configs(default_cfg, custom_cfg)
    """
    logger.debug("Merging configurations")
    return OmegaConf.merge(base_cfg, override_cfg)


# Configuration accessors for specific components


def get_llm_config(cfg: DictConfig) -> Dict[str, Any]:
    """Extract LLM configuration.

    Args:
        cfg: Full configuration object.

    Returns:
        Dictionary with LLM settings.

    Example:
        >>> llm_cfg = get_llm_config(cfg)
        >>> print(llm_cfg['model'])
    """
    llm_cfg = OmegaConf.to_container(cfg.llm, resolve=True)

    # Load API key from environment
    if "openai" in llm_cfg:
        api_key_env = llm_cfg["openai"].get("api_key_env", "OPENAI_API_KEY")
        llm_cfg["api_key"] = os.getenv(api_key_env)
    elif "anthropic" in llm_cfg:
        api_key_env = llm_cfg["anthropic"].get("api_key_env", "ANTHROPIC_API_KEY")
        llm_cfg["api_key"] = os.getenv(api_key_env)

    return llm_cfg


def get_search_config(cfg: DictConfig) -> Dict[str, Any]:
    """Extract search configuration.

    Args:
        cfg: Full configuration object.

    Returns:
        Dictionary with search settings.

    Example:
        >>> search_cfg = get_search_config(cfg)
        >>> print(search_cfg['web']['max_results'])
    """
    search_cfg = OmegaConf.to_container(cfg.search, resolve=True)

    # Load API keys from environment
    if "web" in search_cfg and "tavily" in search_cfg["web"]:
        api_key_env = search_cfg["web"]["tavily"].get("api_key_env", "TAVILY_API_KEY")
        search_cfg["web"]["api_key"] = os.getenv(api_key_env)

    return search_cfg


def get_research_config(cfg: DictConfig) -> Dict[str, Any]:
    """Extract research configuration.

    Args:
        cfg: Full configuration object.

    Returns:
        Dictionary with research settings.

    Example:
        >>> research_cfg = get_research_config(cfg)
        >>> print(research_cfg['max_analysts'])
    """
    return OmegaConf.to_container(cfg.research, resolve=True)


def get_logging_config(cfg: DictConfig) -> Dict[str, Any]:
    """Extract logging configuration.

    Args:
        cfg: Full configuration object.

    Returns:
        Dictionary with logging settings.

    Example:
        >>> log_cfg = get_logging_config(cfg)
        >>> print(log_cfg['level'])
    """
    return OmegaConf.to_container(cfg.logging, resolve=True)


def get_output_config(cfg: DictConfig) -> Dict[str, Any]:
    """Extract output configuration.

    Args:
        cfg: Full configuration object.

    Returns:
        Dictionary with output settings.

    Example:
        >>> output_cfg = get_output_config(cfg)
        >>> print(output_cfg['output_dir'])
    """
    return OmegaConf.to_container(cfg.output, resolve=True)


# Validation functions


def validate_config(cfg: DictConfig) -> bool:
    """Validate configuration completeness and correctness.

    Args:
        cfg: Configuration to validate.

    Returns:
        True if valid, False otherwise.

    Example:
        >>> if validate_config(cfg):
        ...     print("Configuration is valid")
    """
    logger.info("Validating configuration")

    required_sections = ["llm", "search", "research", "logging", "output"]

    for section in required_sections:
        if section not in cfg:
            logger.error(f"Missing required config section: {section}")
            return False

    # Validate LLM config
    if not cfg.llm.get("model"):
        logger.error("LLM model not specified")
        return False

    # Validate research config
    if cfg.research.max_analysts < 1 or cfg.research.max_analysts > 10:
        logger.error("max_analysts must be between 1 and 10")
        return False

    if cfg.research.max_interview_turns < 1:
        logger.error("max_interview_turns must be at least 1")
        return False

    # Validate search config
    if cfg.search.web.enabled and not cfg.search.web.max_results:
        logger.error("web search enabled but max_results not specified")
        return False

    logger.info("Configuration validation passed")
    return True


def print_config(cfg: DictConfig, resolve: bool = True) -> None:
    """Print configuration in a readable format.

    Args:
        cfg: Configuration to print.
        resolve: Whether to resolve interpolations.

    Example:
        >>> print_config(cfg)
    """
    print("=" * 80)
    print("CONFIGURATION")
    print("=" * 80)
    print(OmegaConf.to_yaml(cfg, resolve=resolve))
    print("=" * 80)


# Environment variable helpers


def load_env_file(env_file: str = ".env") -> None:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file.

    Example:
        >>> load_env_file(".env")
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
    except Exception as e:
        logger.warning(f"Failed to load .env file: {str(e)}")


def check_required_env_vars(cfg: DictConfig) -> bool:
    """Check if required environment variables are set.

    Args:
        cfg: Configuration object.

    Returns:
        True if all required vars are set, False otherwise.

    Example:
        >>> if not check_required_env_vars(cfg):
        ...     print("Missing required environment variables")
    """
    required_vars = []

    # Check LLM API keys
    if cfg.llm.provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    elif cfg.llm.provider == "anthropic":
        required_vars.append("ANTHROPIC_API_KEY")

    # Check search API keys
    if cfg.search.web.enabled and cfg.search.web.provider == "tavily":
        required_vars.append("TAVILY_API_KEY")

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False

    logger.info("All required environment variables are set")
    return True


# Configuration templates for common scenarios


def create_quick_research_config(
    topic: str, max_analysts: int = 3, llm_model: str = "gpt-4o"
) -> DictConfig:
    """Create a quick configuration for research.

    Args:
        topic: Research topic.
        max_analysts: Number of analysts.
        llm_model: LLM model to use.

    Returns:
        Configuration ready for research.

    Example:
        >>> cfg = create_quick_research_config("AI Safety", max_analysts=4)
    """
    overrides = [
        f"research.max_analysts={max_analysts}",
        f"llm.model={llm_model}",
        "research.enable_interrupts=false",  # Quick run without interrupts
    ]

    return load_config(overrides=overrides)


def create_development_config() -> DictConfig:
    """Create configuration for development/debugging.

    Returns:
        Development configuration.

    Example:
        >>> cfg = create_development_config()
    """
    overrides = [
        "dev.debug=true",
        "dev.verbose=true",
        "logging.level=DEBUG",
        "search.web.use_cache=false",  # Fresh data
        "research.max_analysts=2",  # Faster execution
        "research.max_interview_turns=1",
    ]

    return load_config(overrides=overrides)


def create_production_config() -> DictConfig:
    """Create configuration for production use.

    Returns:
        Production configuration.

    Example:
        >>> cfg = create_production_config()
    """
    overrides = [
        "dev.debug=false",
        "logging.level=INFO",
        "logging.structured=true",  # JSON logging
        "search.web.use_cache=true",
        "checkpointing.enabled=true",
        "performance.parallel_interviews=true",
    ]

    return load_config(overrides=overrides)
