"""State management for the research assistant graph workflows.

This module defines all state structures used throughout the LangGraph workflows,
including state for analyst generation, interviews, and the overall research process.
It also provides utilities for state validation, transformation, and serialization.

Example:
    Creating and validating research state:

    >>> from research_assistant.core.schemas import Analyst
    >>> state = ResearchGraphState(
    ...     topic="AI Safety",
    ...     max_analysts=3,
    ...     analysts=[],
    ...     sections=[],
    ...     introduction="",
    ...     content="",
    ...     conclusion="",
    ...     final_report=""
    ... )
    >>> is_valid = validate_research_state(state)
"""

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import MessagesState

from .schemas import Analyst


class WorkflowStage(str, Enum):
    """Enumeration of workflow stages for tracking progress.

    These stages help identify where the research process is currently
    at and enable proper state management and debugging.
    """

    INITIAL = "initial"
    CREATING_ANALYSTS = "creating_analysts"
    AWAITING_FEEDBACK = "awaiting_feedback"
    CONDUCTING_INTERVIEWS = "conducting_interviews"
    WRITING_SECTIONS = "writing_sections"
    WRITING_REPORT = "writing_report"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ERROR = "error"


class GenerateAnalystsState(TypedDict, total=False):
    """State for the analyst generation phase.

    This state tracks the creation and approval of analyst personas who will
    conduct the research interviews.

    Attributes:
        topic: The research topic to investigate.
        max_analysts: Maximum number of analyst personas to create.
        human_analyst_feedback: Human feedback on generated analysts.
            Use 'approve' to proceed or provide feedback for regeneration.
        analysts: List of generated Analyst instances.

    Example:
        >>> state: GenerateAnalystsState = {
        ...     "topic": "Quantum Computing Applications",
        ...     "max_analysts": 3,
        ...     "human_analyst_feedback": "approve",
        ...     "analysts": []
        ... }
    """

    topic: str
    max_analysts: int
    human_analyst_feedback: str
    analysts: List[Analyst]


class InterviewState(MessagesState, total=False):
    """State for individual analyst interview sessions.

    This state extends MessagesState to track the conversation between an
    analyst and an expert, along with retrieved context and metadata.

    Attributes:
        max_num_turns: Maximum number of question-answer turns in the interview.
        context: Accumulated source documents from searches. Uses operator.add
            to append new documents to the list.
        analyst: The Analyst conducting the interview.
        interview: Complete transcript of the interview conversation.
        sections: Final report sections generated from the interview.

    Note:
        Inherits 'messages' from MessagesState for conversation history.

    Example:
        >>> from langchain_core.messages import HumanMessage
        >>> state: InterviewState = {
        ...     "messages": [HumanMessage(content="Let's discuss AI safety")],
        ...     "max_num_turns": 2,
        ...     "context": [],
        ...     "analyst": analyst_instance,
        ...     "interview": "",
        ...     "sections": []
        ... }
    """

    max_num_turns: int
    context: Annotated[list, operator.add]
    analyst: Analyst
    interview: str
    sections: list


class ResearchGraphState(TypedDict, total=False):
    """State for the overall research workflow.

    This is the top-level state that orchestrates the entire research process,
    from analyst creation through interview execution to final report generation.

    Attributes:
        topic: The research topic to investigate.
        max_analysts: Maximum number of analyst personas to create.
        human_analyst_feedback: Human feedback on generated analysts.
        analysts: List of generated Analyst instances.
        sections: Report sections from all interviews. Uses operator.add
            to accumulate sections from parallel interviews.
        introduction: Generated introduction for the final report.
        content: Main content/insights section of the final report.
        conclusion: Generated conclusion for the final report.
        final_report: Complete assembled final report in markdown format.

    Example:
        >>> state: ResearchGraphState = {
        ...     "topic": "Large Language Models",
        ...     "max_analysts": 3,
        ...     "human_analyst_feedback": "approve",
        ...     "analysts": [],
        ...     "sections": [],
        ...     "introduction": "",
        ...     "content": "",
        ...     "conclusion": "",
        ...     "final_report": ""
        ... }
    """

    topic: str
    max_analysts: int
    human_analyst_feedback: str
    analysts: List[Analyst]
    sections: Annotated[list, operator.add]
    introduction: str
    content: str
    conclusion: str
    final_report: str


@dataclass
class StateMetadata:
    """Metadata for tracking state evolution and debugging.

    This class helps track how state changes over time, which is useful
    for debugging, monitoring, and understanding the workflow execution.

    Attributes:
        stage: Current workflow stage.
        timestamp: ISO format timestamp of state creation/update.
        node_name: Name of the node that created this state.
        error: Error message if an error occurred.
        token_count: Approximate token count used so far.
        api_calls: Number of API calls made so far.

    Example:
        >>> metadata = StateMetadata(
        ...     stage=WorkflowStage.CONDUCTING_INTERVIEWS,
        ...     node_name="generate_question",
        ...     token_count=1500,
        ...     api_calls=3
        ... )
    """

    stage: WorkflowStage = WorkflowStage.INITIAL
    timestamp: str = ""
    node_name: str = ""
    error: Optional[str] = None
    token_count: int = 0
    api_calls: int = 0
    custom_data: Dict[str, Any] = field(default_factory=dict)


# State Validation Functions


def validate_generate_analysts_state(state: GenerateAnalystsState) -> bool:
    """Validate the GenerateAnalystsState structure and content.

    Args:
        state: The state dictionary to validate.

    Returns:
        True if state is valid, False otherwise.

    Raises:
        ValueError: If required fields are missing or invalid.

    Example:
        >>> state = {"topic": "AI", "max_analysts": 3, "analysts": []}
        >>> validate_generate_analysts_state(state)
        True
    """
    # Check required fields
    required_fields = {"topic", "max_analysts"}
    missing_fields = required_fields - set(state.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    # Validate topic
    if not state["topic"] or not state["topic"].strip():
        raise ValueError("Topic cannot be empty")

    if len(state["topic"]) < 3:
        raise ValueError("Topic must be at least 3 characters long")

    # Validate max_analysts
    if not isinstance(state["max_analysts"], int):
        raise ValueError("max_analysts must be an integer")

    if state["max_analysts"] < 1 or state["max_analysts"] > 10:
        raise ValueError("max_analysts must be between 1 and 10")

    # Validate analysts list if present
    if "analysts" in state:
        if not isinstance(state["analysts"], list):
            raise ValueError("analysts must be a list")

        if len(state["analysts"]) > state["max_analysts"]:
            raise ValueError(
                f"Number of analysts ({len(state['analysts'])}) exceeds "
                f"max_analysts ({state['max_analysts']})"
            )

    return True


def validate_interview_state(state: InterviewState) -> bool:
    """Validate the InterviewState structure and content.

    Args:
        state: The state dictionary to validate.

    Returns:
        True if state is valid, False otherwise.

    Raises:
        ValueError: If required fields are missing or invalid.

    Example:
        >>> state = {
        ...     "messages": [],
        ...     "analyst": analyst,
        ...     "max_num_turns": 2,
        ...     "context": []
        ... }
        >>> validate_interview_state(state)
        True
    """
    # Check required fields
    required_fields = {"messages", "analyst"}
    missing_fields = required_fields - set(state.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    # Validate messages
    if not isinstance(state["messages"], list):
        raise ValueError("messages must be a list")

    # Validate analyst
    if not isinstance(state["analyst"], Analyst):
        raise ValueError("analyst must be an Analyst instance")

    # Validate max_num_turns if present
    if "max_num_turns" in state:
        if not isinstance(state["max_num_turns"], int):
            raise ValueError("max_num_turns must be an integer")

        if state["max_num_turns"] < 1 or state["max_num_turns"] > 10:
            raise ValueError("max_num_turns must be between 1 and 10")

    # Validate context if present
    if "context" in state:
        if not isinstance(state["context"], list):
            raise ValueError("context must be a list")

    return True


def validate_research_state(state: ResearchGraphState) -> bool:
    """Validate the ResearchGraphState structure and content.

    Args:
        state: The state dictionary to validate.

    Returns:
        True if state is valid, False otherwise.

    Raises:
        ValueError: If required fields are missing or invalid.

    Example:
        >>> state = {
        ...     "topic": "AI Safety",
        ...     "max_analysts": 3,
        ...     "analysts": [],
        ...     "sections": []
        ... }
        >>> validate_research_state(state)
        True
    """
    # Check required fields
    required_fields = {"topic", "max_analysts"}
    missing_fields = required_fields - set(state.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    # Validate topic
    if not state["topic"] or not state["topic"].strip():
        raise ValueError("Topic cannot be empty")

    # Validate max_analysts
    if not isinstance(state["max_analysts"], int):
        raise ValueError("max_analysts must be an integer")

    if state["max_analysts"] < 1 or state["max_analysts"] > 10:
        raise ValueError("max_analysts must be between 1 and 10")

    # Validate analysts list if present
    if "analysts" in state:
        if not isinstance(state["analysts"], list):
            raise ValueError("analysts must be a list")

        for analyst in state["analysts"]:
            if not isinstance(analyst, Analyst):
                raise ValueError("All analysts must be Analyst instances")

    # Validate sections if present
    if "sections" in state:
        if not isinstance(state["sections"], list):
            raise ValueError("sections must be a list")

    return True


# State Transformation Functions


def create_initial_research_state(
    topic: str, max_analysts: int = 3, human_analyst_feedback: str = ""
) -> ResearchGraphState:
    """Create an initial ResearchGraphState with default values.

    Args:
        topic: The research topic to investigate.
        max_analysts: Maximum number of analyst personas to create. Defaults to 3.
        human_analyst_feedback: Initial feedback. Defaults to empty string.

    Returns:
        A new ResearchGraphState dictionary with all fields initialized.

    Raises:
        ValueError: If inputs are invalid.

    Example:
        >>> state = create_initial_research_state("Quantum Computing", max_analysts=4)
        >>> state["topic"]
        'Quantum Computing'
        >>> state["max_analysts"]
        4
    """
    # Validate inputs
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")

    if max_analysts < 1 or max_analysts > 10:
        raise ValueError("max_analysts must be between 1 and 10")

    state: ResearchGraphState = {
        "topic": topic.strip(),
        "max_analysts": max_analysts,
        "human_analyst_feedback": human_analyst_feedback,
        "analysts": [],
        "sections": [],
        "introduction": "",
        "content": "",
        "conclusion": "",
        "final_report": "",
    }

    return state


def create_interview_state(
    analyst: Analyst, initial_message: str, max_num_turns: int = 2
) -> InterviewState:
    """Create an initial InterviewState for an analyst interview.

    Args:
        analyst: The Analyst conducting the interview.
        initial_message: The opening message to start the interview.
        max_num_turns: Maximum number of question-answer turns. Defaults to 2.

    Returns:
        A new InterviewState dictionary with all fields initialized.

    Raises:
        ValueError: If inputs are invalid.

    Example:
        >>> state = create_interview_state(
        ...     analyst=my_analyst,
        ...     initial_message="Let's discuss AI safety",
        ...     max_num_turns=3
        ... )
    """
    if not isinstance(analyst, Analyst):
        raise ValueError("analyst must be an Analyst instance")

    if not initial_message or not initial_message.strip():
        raise ValueError("initial_message cannot be empty")

    if max_num_turns < 1 or max_num_turns > 10:
        raise ValueError("max_num_turns must be between 1 and 10")

    state: InterviewState = {
        "messages": [HumanMessage(content=initial_message.strip())],
        "max_num_turns": max_num_turns,
        "context": [],
        "analyst": analyst,
        "interview": "",
        "sections": [],
    }

    return state


# State Inspection Functions


def get_interview_turn_count(state: InterviewState) -> int:
    """Count the number of completed interview turns.

    A turn consists of a question from the analyst (HumanMessage) followed by
    an answer from the expert (AIMessage with name='expert').

    Args:
        state: The interview state to inspect.

    Returns:
        Number of completed question-answer turns.

    Example:
        >>> turn_count = get_interview_turn_count(state)
        >>> print(f"Completed {turn_count} turns")
    """
    messages = state.get("messages", [])
    expert_responses = [m for m in messages if isinstance(m, AIMessage) and m.name == "expert"]
    return len(expert_responses)


def get_total_context_length(state: InterviewState) -> int:
    """Calculate the total character length of all context documents.

    Args:
        state: The interview state to inspect.

    Returns:
        Total number of characters across all context documents.

    Example:
        >>> context_length = get_total_context_length(state)
        >>> print(f"Total context: {context_length} characters")
    """
    context = state.get("context", [])
    return sum(len(doc) for doc in context if isinstance(doc, str))


def get_research_progress(state: ResearchGraphState) -> Dict[str, Any]:
    """Get a summary of research progress.

    Args:
        state: The research state to inspect.

    Returns:
        Dictionary containing progress metrics:
        - analysts_created: Number of analysts created
        - interviews_completed: Number of sections (completed interviews)
        - has_introduction: Whether introduction is written
        - has_content: Whether main content is written
        - has_conclusion: Whether conclusion is written
        - has_final_report: Whether final report is complete

    Example:
        >>> progress = get_research_progress(state)
        >>> print(f"Progress: {progress['interviews_completed']} interviews done")
    """
    return {
        "analysts_created": len(state.get("analysts", [])),
        "interviews_completed": len(state.get("sections", [])),
        "has_introduction": bool(state.get("introduction", "").strip()),
        "has_content": bool(state.get("content", "").strip()),
        "has_conclusion": bool(state.get("conclusion", "").strip()),
        "has_final_report": bool(state.get("final_report", "").strip()),
    }


def is_research_complete(state: ResearchGraphState) -> bool:
    """Check if the research workflow is complete.

    Args:
        state: The research state to check.

    Returns:
        True if final report is generated, False otherwise.

    Example:
        >>> if is_research_complete(state):
        ...     print("Research complete! Report ready.")
    """
    return bool(state.get("final_report", "").strip())


# State Serialization Functions


def serialize_state_for_checkpoint(state: ResearchGraphState) -> Dict[str, Any]:
    """Serialize state for checkpointing/persistence.

    Converts state to a JSON-serializable format by handling Pydantic models
    and other complex types.

    Args:
        state: The state to serialize.

    Returns:
        JSON-serializable dictionary.

    Example:
        >>> serialized = serialize_state_for_checkpoint(state)
        >>> import json
        >>> json.dumps(serialized)  # Can now be saved
    """
    serialized = dict(state)

    # Convert Analyst objects to dictionaries
    if "analysts" in serialized:
        serialized["analysts"] = [analyst.model_dump() for analyst in serialized["analysts"]]

    return serialized


def deserialize_state_from_checkpoint(data: Dict[str, Any]) -> ResearchGraphState:
    """Deserialize state from a checkpoint.

    Reconstructs state from a JSON-serializable format, converting
    dictionaries back to Pydantic models.

    Args:
        data: The serialized state data.

    Returns:
        Reconstructed ResearchGraphState.

    Example:
        >>> import json
        >>> data = json.loads(checkpoint_json)
        >>> state = deserialize_state_from_checkpoint(data)
    """
    state = ResearchGraphState(**data)

    # Convert analyst dictionaries back to Analyst objects
    if "analysts" in state and state["analysts"]:
        if isinstance(state["analysts"][0], dict):
            state["analysts"] = [Analyst(**analyst_dict) for analyst_dict in state["analysts"]]

    return state


# Utility function for state updates


def merge_state_updates(current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge state updates with special handling for annotated fields.

    This function properly handles fields with Annotated[list, operator.add]
    by appending rather than replacing.

    Args:
        current_state: The current state dictionary.
        updates: Dictionary of updates to apply.

    Returns:
        New state dictionary with updates applied.

    Example:
        >>> new_state = merge_state_updates(
        ...     current_state={"sections": ["intro"]},
        ...     updates={"sections": ["body"]}
        ... )
        >>> new_state["sections"]
        ['intro', 'body']
    """
    new_state = current_state.copy()

    # Fields that use operator.add (append instead of replace)
    additive_fields = {"context", "sections"}

    for key, value in updates.items():
        if key in additive_fields and key in new_state:
            # Append to existing list
            if isinstance(value, list):
                new_state[key] = new_state[key] + value
            else:
                new_state[key] = new_state[key] + [value]
        else:
            # Replace value
            new_state[key] = value

    return new_state
