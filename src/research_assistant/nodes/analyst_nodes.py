"""Node functions for analyst creation and management.

This module contains LangGraph node functions responsible for creating analyst
personas and handling human feedback during the analyst generation process.

Example:
    >>> from research_assistant.nodes.analyst_nodes import create_analysts
    >>> from research_assistant.core.state import GenerateAnalystsState
    >>>
    >>> state = {
    ...     "topic": "AI Safety",
    ...     "max_analysts": 3,
    ...     "human_analyst_feedback": ""
    ... }
    >>> result = create_analysts(state)
    >>> print(f"Created {len(result['analysts'])} analysts")
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..core.schemas import Analyst, Perspectives
from ..core.state import GenerateAnalystsState
from ..prompts.analyst_prompts import format_analyst_instructions

# Configure logger
logger = logging.getLogger(__name__)


class AnalystCreationError(Exception):
    """Raised when analyst creation fails."""

    pass


def create_analysts(
    state: GenerateAnalystsState, llm: Optional[ChatOpenAI] = None, detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Create analyst personas based on research topic and feedback.

    This node generates a diverse set of analyst personas who will conduct
    research interviews. Each analyst represents a unique perspective on the
    research topic.

    Args:
        state: Current state containing topic, max_analysts, and optional
            human_analyst_feedback.
        llm: Optional LLM instance. If None, creates default ChatOpenAI instance.
        detailed_prompts: If True, use more detailed prompt instructions.
            Defaults to False.

    Returns:
        Dictionary with 'analysts' key containing list of Analyst instances.

    Raises:
        AnalystCreationError: If analyst creation fails.
        ValueError: If state is missing required fields.

    Example:
        >>> state = {
        ...     "topic": "Quantum Computing Applications",
        ...     "max_analysts": 3,
        ...     "human_analyst_feedback": ""
        ... }
        >>> result = create_analysts(state)
        >>> print(result['analysts'][0].name)
    """
    logger.info("Starting analyst creation process")

    # Extract state variables
    topic = state.get("topic")
    max_analysts = state.get("max_analysts")
    human_analyst_feedback = state.get("human_analyst_feedback", "")

    # Validate required fields
    if not topic:
        raise ValueError("Topic is required for analyst creation")

    if not max_analysts:
        raise ValueError("max_analysts is required for analyst creation")

    # Validate max_analysts is within acceptable range
    if max_analysts < 1 or max_analysts > 10:
        raise ValueError("max_analysts must be between 1 and 10")

    if not isinstance(max_analysts, int) or max_analysts < 1:
        raise ValueError(f"max_analysts must be positive integer, got {max_analysts}")

    logger.debug(
        f"Creating analysts for topic='{topic}', "
        f"max_analysts={max_analysts}, "
        f"feedback_provided={bool(human_analyst_feedback)}"
    )

    # Initialize LLM if not provided
    if llm is None:
        logger.debug("Initializing default LLM (gpt-4o)")
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Enforce structured output
    structured_llm = llm.with_structured_output(Perspectives)

    # Format system message
    system_message_content = format_analyst_instructions(
        topic=topic,
        max_analysts=max_analysts,
        human_feedback=human_analyst_feedback,
        detailed=detailed_prompts,
    )

    logger.debug(f"System message length: {len(system_message_content)} chars")

    # Create messages
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content="Generate the set of analysts."),
    ]

    # Generate analysts
    try:
        logger.info("Invoking LLM for analyst generation")
        perspectives = structured_llm.invoke(messages)

        if not isinstance(perspectives, Perspectives):
            raise AnalystCreationError(f"Expected Perspectives object, got {type(perspectives)}")

        analysts = perspectives.analysts

        # Validate we got analysts
        if not analysts:
            raise AnalystCreationError("LLM returned empty analyst list")

        if len(analysts) > max_analysts:
            logger.warning(
                f"LLM generated {len(analysts)} analysts, "
                f"expected max {max_analysts}. Truncating."
            )
            analysts = analysts[:max_analysts]

        logger.info(f"Successfully created {len(analysts)} analysts")

        # Log analyst summary
        for i, analyst in enumerate(analysts, 1):
            logger.debug(f"Analyst {i}: {analyst.name} - {analyst.role} at {analyst.affiliation}")

        return {"analysts": analysts}

    except Exception as e:
        logger.error(f"Failed to create analysts: {str(e)}", exc_info=True)
        raise AnalystCreationError(f"Analyst creation failed: {str(e)}") from e


def human_feedback(state: GenerateAnalystsState) -> Dict[str, Any]:
    """No-op node that should be interrupted on for human feedback.

    This is a placeholder node where the graph will be interrupted to allow
    human review and feedback on the generated analysts. The LangGraph
    interrupt mechanism will pause execution here.

    Args:
        state: Current state (passed through unchanged).

    Returns:
        Empty dictionary (no state updates).

    Note:
        This node is designed to be used with LangGraph's interrupt_before
        configuration. When the graph is compiled with
        interrupt_before=['human_feedback'], execution will pause here
        to allow human intervention.

    Example:
        >>> # In graph configuration
        >>> graph = builder.compile(interrupt_before=['human_feedback'])
        >>> # Graph will pause at this node for human review
    """
    logger.info("Human feedback node reached (no-op for interrupt)")
    # This is intentionally a no-op - the graph interrupts here
    return {}


def validate_analyst_feedback(feedback: str) -> bool:
    """Validate human feedback on analysts.

    Checks if the feedback is in the expected format. Feedback can either be
    'approve' to proceed, or any other string to trigger regeneration.

    Args:
        feedback: The human feedback string.

    Returns:
        True if feedback is 'approve', False otherwise.

    Example:
        >>> validate_analyst_feedback("approve")
        True
        >>> validate_analyst_feedback("Need more technical experts")
        False
    """
    if not feedback:
        logger.warning("Empty feedback received, treating as approval")
        return True

    is_approved = feedback.lower().strip() == "approve"

    if is_approved:
        logger.info("Analysts approved by human reviewer")
    else:
        logger.info(f"Analysts require regeneration. Feedback: {feedback[:100]}")

    return is_approved


def format_analysts_for_review(analysts: list[Analyst]) -> str:
    """Format analyst list for human review.

    Creates a readable text representation of analysts for review purposes.

    Args:
        analysts: List of Analyst instances.

    Returns:
        Formatted string describing all analysts.

    Example:
        >>> formatted = format_analysts_for_review(analysts)
        >>> print(formatted)
        ANALYST TEAM (3 members)
        ========================

        1. Dr. Sarah Chen
           Role: Machine Learning Researcher
           Affiliation: Google DeepMind
           Focus: Specializes in transformer architectures...
    """
    if not analysts:
        return "No analysts generated."

    lines = [f"ANALYST TEAM ({len(analysts)} members)", "=" * 50, ""]

    for i, analyst in enumerate(analysts, 1):
        lines.extend(
            [
                f"{i}. {analyst.name}",
                f"   Role: {analyst.role}",
                f"   Affiliation: {analyst.affiliation}",
                f"   Focus: {analyst.description[:100]}{'...' if len(analyst.description) > 100 else ''}",
                "",
            ]
        )

    return "\n".join(lines)


def get_analyst_diversity_metrics(analysts: list[Analyst]) -> Dict[str, Any]:
    """Calculate diversity metrics for a list of analysts.

    Analyzes the analyst team to assess diversity across various dimensions.

    Args:
        analysts: List of Analyst instances.

    Returns:
        Dictionary containing diversity metrics:
        - unique_roles: Number of unique roles
        - unique_affiliations: Number of unique affiliations
        - role_diversity_ratio: Ratio of unique roles to total analysts
        - affiliation_diversity_ratio: Ratio of unique affiliations to total

    Example:
        >>> metrics = get_analyst_diversity_metrics(analysts)
        >>> print(f"Role diversity: {metrics['role_diversity_ratio']:.2f}")
    """
    if not analysts:
        return {
            "total_analysts": 0,
            "unique_roles": 0,
            "unique_affiliations": 0,
            "role_diversity_ratio": 0.0,
            "affiliation_diversity_ratio": 0.0,
        }

    roles = [a.role for a in analysts]
    affiliations = [a.affiliation for a in analysts]

    unique_roles = len(set(roles))
    unique_affiliations = len(set(affiliations))

    total = len(analysts)

    return {
        "unique_roles": unique_roles,
        "unique_affiliations": unique_affiliations,
        "role_diversity_ratio": unique_roles / total,
        "affiliation_diversity_ratio": unique_affiliations / total,
        "total_analysts": total,
    }


def regenerate_analysts_with_feedback(
    state: GenerateAnalystsState, llm: Optional[ChatOpenAI] = None
) -> Dict[str, Any]:
    """Regenerate analysts based on human feedback.

    This is a specialized version of create_analysts that emphasizes
    incorporating human feedback into the regeneration process.

    Args:
        state: State containing topic, max_analysts, and human_analyst_feedback.
        llm: Optional LLM instance.

    Returns:
        Dictionary with updated 'analysts' list.

    Raises:
        ValueError: If human_analyst_feedback is missing.

    Example:
        >>> state = {
        ...     "topic": "AI Safety",
        ...     "max_analysts": 3,
        ...     "human_analyst_feedback": "Need more policy experts"
        ... }
        >>> result = regenerate_analysts_with_feedback(state)
    """
    feedback = state.get("human_analyst_feedback", "")

    if not feedback or feedback.lower().strip() == "approve":
        raise ValueError(
            "Regeneration requires specific feedback. "
            "Use 'approve' only to proceed with current analysts."
        )

    logger.info(f"Regenerating analysts with feedback: {feedback[:100]}")

    # Use detailed prompts for regeneration to better incorporate feedback
    return create_analysts(state, llm=llm, detailed_prompts=True)


# Node configuration helpers


def get_analyst_node_config() -> Dict[str, Any]:
    """Get recommended configuration for analyst nodes.

    Returns:
        Dictionary containing configuration recommendations.

    Example:
        >>> config = get_analyst_node_config()
        >>> print(config['recommended_temperature'])
    """
    return {
        "recommended_temperature": 0,  # Deterministic for consistency
        "recommended_model": "gpt-4o",
        "max_retries": 3,
        "timeout_seconds": 60,
        "interrupt_node": "human_feedback",
        "detailed_prompts_for_regeneration": True,
    }
