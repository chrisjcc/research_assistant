"""Node functions for conducting analyst interviews.

This module contains LangGraph node functions for the interview process,
including question generation, answer generation, and interview management.

Example:
    >>> from research_assistant.nodes.interview_nodes import generate_question
    >>> from research_assistant.core.state import InterviewState
    >>> 
    >>> result = generate_question(state)
    >>> print(result['messages'][-1].content)
"""

import logging
from typing import Dict, Any, List, Optional, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages import get_buffer_string
from langchain_openai import ChatOpenAI

from ..core.state import InterviewState
from ..core.schemas import Analyst
from ..prompts.interview_prompts import (
    format_question_instructions,
    format_answer_instructions,
    is_interview_complete,
)


# Configure logger
logger = logging.getLogger(__name__)


class InterviewError(Exception):
    """Raised when interview operations fail."""
    pass


def generate_question(
    state: InterviewState,
    llm: Optional[ChatOpenAI] = None,
    detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Generate the next interview question from the analyst.
    
    This node generates a question based on the analyst's persona and the
    conversation history. The analyst asks questions to gather specific
    insights related to their focus area.
    
    Args:
        state: Current interview state with analyst, messages, and context.
        llm: Optional LLM instance. If None, creates default.
        detailed_prompts: If True, use more detailed instructions.
        
    Returns:
        Dictionary with 'messages' containing the new question.
        
    Raises:
        InterviewError: If question generation fails.
        ValueError: If required state fields are missing.
        
    Example:
        >>> state = {
        ...     "analyst": analyst_instance,
        ...     "messages": [HumanMessage(content="Let's start")]
        ... }
        >>> result = generate_question(state)
    """
    logger.info("Generating interview question")
    
    # Extract state
    analyst = state.get("analyst")
    messages = state.get("messages", [])
    
    # Validate state
    if not analyst:
        raise ValueError("Analyst is required in state")
    
    if not isinstance(analyst, Analyst):
        raise ValueError(f"Expected Analyst instance, got {type(analyst)}")
    
    if not isinstance(messages, list):
        raise ValueError(f"messages must be a list, got {type(messages)}")
    
    logger.debug(
        f"Generating question for analyst: {analyst.name}, "
        f"conversation_length={len(messages)}"
    )
    
    # Initialize LLM if needed
    if llm is None:
        logger.debug("Initializing default LLM")
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Format system message
    system_message_content = format_question_instructions(
        analyst_persona=analyst.persona,
        detailed=detailed_prompts
    )
    
    # Create message list
    llm_messages = [SystemMessage(content=system_message_content)] + messages
    
    try:
        logger.info("Invoking LLM for question generation")
        question = llm.invoke(llm_messages)
        
        if not isinstance(question, AIMessage):
            logger.warning(f"Expected AIMessage, got {type(question)}, converting")
            question = AIMessage(content=str(question))
        
        logger.debug(f"Generated question length: {len(question.content)} chars")
        
        # Check if this is the concluding message
        if is_interview_complete(question.content):
            logger.info("Analyst has concluded the interview")
        
        return {"messages": [question]}
        
    except Exception as e:
        logger.error(f"Failed to generate question: {str(e)}", exc_info=True)
        raise InterviewError(f"Question generation failed: {str(e)}") from e


def generate_answer(
    state: InterviewState,
    llm: Optional[ChatOpenAI] = None,
    detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Generate expert answer based on retrieved context.
    
    This node generates an answer from the expert persona, using only
    information from the retrieved context documents. The answer includes
    proper citations.
    
    Args:
        state: Current interview state with analyst, messages, and context.
        llm: Optional LLM instance.
        detailed_prompts: If True, use more detailed instructions.
        
    Returns:
        Dictionary with 'messages' containing the expert's answer.
        
    Raises:
        InterviewError: If answer generation fails.
        ValueError: If required state fields are missing.
        
    Example:
        >>> state = {
        ...     "analyst": analyst_instance,
        ...     "messages": [question_message],
        ...     "context": ["<Document>...</Document>"]
        ... }
        >>> result = generate_answer(state)
    """
    logger.info("Generating expert answer")
    
    # Extract state
    analyst = state.get("analyst")
    messages = state.get("messages", [])
    context = state.get("context", [])
    
    # Validate state
    if not analyst:
        raise ValueError("Analyst is required in state")
    
    if not isinstance(analyst, Analyst):
        raise ValueError(f"Expected Analyst instance, got {type(analyst)}")
    
    if not context:
        logger.warning("No context provided for answer generation")
    
    logger.debug(
        f"Generating answer for analyst: {analyst.name}, "
        f"context_docs={len(context)}, "
        f"messages={len(messages)}"
    )
    
    # Initialize LLM if needed
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Format context as a single string
    context_str = "\n\n".join(str(doc) for doc in context)
    
    # Format system message
    system_message_content = format_answer_instructions(
        analyst_persona=analyst.persona,
        context=context_str,
        detailed=detailed_prompts
    )
    
    # Create message list
    llm_messages = [SystemMessage(content=system_message_content)] + messages
    
    try:
        logger.info("Invoking LLM for answer generation")
        answer = llm.invoke(llm_messages)
        
        if not isinstance(answer, AIMessage):
            answer = AIMessage(content=str(answer))
        
        # Set the name to identify this as expert response
        answer.name = "expert"
        
        logger.debug(f"Generated answer length: {len(answer.content)} chars")
        logger.info("Successfully generated expert answer")
        
        return {"messages": [answer]}
        
    except Exception as e:
        logger.error(f"Failed to generate answer: {str(e)}", exc_info=True)
        raise InterviewError(f"Answer generation failed: {str(e)}") from e


def save_interview(state: InterviewState) -> Dict[str, Any]:
    """Save the interview transcript to state.
    
    Converts the message history into a formatted string transcript and
    saves it to the interview field.
    
    Args:
        state: Current interview state with messages.
        
    Returns:
        Dictionary with 'interview' containing the transcript string.
        
    Example:
        >>> result = save_interview(state)
        >>> print(result['interview'][:100])
    """
    logger.info("Saving interview transcript")
    
    # Get messages
    messages = state.get("messages", [])
    
    if not messages:
        logger.warning("No messages to save")
        return {"interview": ""}
    
    # Convert to string
    try:
        interview = get_buffer_string(messages)
        
        logger.debug(f"Saved interview transcript: {len(interview)} chars")
        logger.info(f"Interview saved with {len(messages)} messages")
        
        return {"interview": interview}
        
    except Exception as e:
        logger.error(f"Failed to save interview: {str(e)}", exc_info=True)
        # Return empty interview rather than failing
        return {"interview": ""}


def route_messages(
    state: InterviewState,
    expert_name: str = "expert"
) -> Literal["ask_question", "save_interview"]:
    """Route between asking questions and ending the interview.
    
    Determines whether to continue the interview (ask another question) or
    end it (save the interview). The decision is based on:
    1. Maximum number of turns reached
    2. Analyst has concluded the interview
    
    Args:
        state: Current interview state.
        expert_name: Name attribute of expert messages. Defaults to "expert".
        
    Returns:
        Either "ask_question" to continue or "save_interview" to end.
        
    Example:
        >>> next_node = route_messages(state)
        >>> print(f"Next: {next_node}")
    """
    logger.debug("Routing interview decision")
    
    # Get state
    messages = state.get("messages", [])
    max_num_turns = state.get("max_num_turns", 2)
    
    # Count expert responses (completed turns)
    num_responses = len([
        m for m in messages
        if isinstance(m, AIMessage) and getattr(m, 'name', None) == expert_name
    ])
    
    logger.debug(
        f"Interview routing: {num_responses} responses out of {max_num_turns} max turns"
    )
    
    # Check if analyst has concluded (look for conclusion phrases in last message)
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, HumanMessage):
            conclusion_phrases = [
                "thank you", "thanks", "that's all", 
                "that'll be all", "goodbye", "that's everything"
            ]
            content_lower = last_message.content.lower()
            if any(phrase in content_lower for phrase in conclusion_phrases):
                logger.info("Interview concluded by analyst")
                return "save_interview"
    
    # Continue if we haven't reached max turns yet
    # CRITICAL FIX: Use < instead of >= 
    if num_responses < max_num_turns:
        logger.debug("Continuing interview")
        return "ask_question"
    else:
        logger.info(f"Max turns ({max_num_turns}) reached")
        return "save_interview"


def get_interview_statistics(state: InterviewState) -> Dict[str, Any]:
    """Get statistics about the current interview.
    
    Args:
        state: Current interview state.
        
    Returns:
        Dictionary containing interview statistics.
        
    Example:
        >>> stats = get_interview_statistics(state)
        >>> print(f"Questions asked: {stats['num_questions']}")
    """
    messages = state.get("messages", [])
    context = state.get("context", [])
    analyst = state.get("analyst")
    
    # Count messages by type
    num_questions = len([
        m for m in messages 
        if isinstance(m, (HumanMessage, AIMessage)) and m.name != "expert"
    ])
    
    num_answers = len([
        m for m in messages 
        if isinstance(m, AIMessage) and m.name == "expert"
    ])
    
    # Calculate context size
    total_context_chars = sum(len(str(doc)) for doc in context)
    
    return {
        "analyst_name": analyst.name if analyst else "Unknown",
        "num_questions": num_questions,
        "num_answers": num_answers,
        "num_context_docs": len(context),
        "total_context_chars": total_context_chars,
        "total_messages": len(messages),
        "is_complete": num_answers >= state.get("max_num_turns", 2)
    }


def format_interview_summary(state: InterviewState) -> str:
    """Format a human-readable summary of the interview.
    
    Args:
        state: Interview state to summarize.
        
    Returns:
        Formatted summary string.
        
    Example:
        >>> summary = format_interview_summary(state)
        >>> print(summary)
    """
    stats = get_interview_statistics(state)
    analyst = state.get("analyst")
    
    lines = [
        f"Interview Summary",
        "=" * 50,
        f"Analyst: {stats['analyst_name']}",
        f"Role: {analyst.role if analyst else 'Unknown'}",
        f"Questions Asked: {stats['num_questions']}",
        f"Answers Received: {stats['num_answers']}",
        f"Context Documents: {stats['num_context_docs']}",
        f"Total Context Size: {stats['total_context_chars']:,} characters",
        f"Status: {'Complete' if stats['is_complete'] else 'In Progress'}"
    ]
    
    return "\n".join(lines)


def extract_citations_from_interview(interview_text: str) -> List[str]:
    """Extract all citations from an interview transcript.
    
    Args:
        interview_text: The interview transcript string.
        
    Returns:
        List of unique citation numbers found (e.g., ['1', '2', '3']).
        
    Example:
        >>> citations = extract_citations_from_interview(transcript)
        >>> print(f"Found {len(citations)} unique sources")
    """
    import re
    
    # Pattern to match [N] or [N,M] or [N,M,O] etc.
    pattern = r'\[(\d+(?:,\s*\d+)*)\]'
    matches = re.findall(pattern, interview_text)
    
    # Extract individual numbers
    citations = set()
    for match in matches:
        numbers = match.split(',')
        citations.update(n.strip() for n in numbers)
    
    return sorted(citations, key=int)


# Interview quality assessment

def assess_interview_quality(state: InterviewState) -> Dict[str, Any]:
    """Assess the quality of a completed interview.
    
    Provides metrics and indicators of interview quality based on various
    heuristics.
    
    Args:
        state: Completed interview state.
        
    Returns:
        Dictionary containing quality assessment metrics.
        
    Example:
        >>> quality = assess_interview_quality(state)
        >>> print(f"Quality score: {quality['overall_score']}/10")
    """
    messages = state.get("messages", [])
    interview = state.get("interview", "")
    context = state.get("context", [])
    
    # Calculate metrics
    stats = get_interview_statistics(state)
    citations = extract_citations_from_interview(interview)
    
    # Heuristic scoring
    scores = {
        "context_coverage": min(10, len(context) * 3),  # More context is good
        "citation_usage": min(10, len(citations) * 2),  # More citations is good
        "depth": min(10, stats["num_answers"] * 5),  # More turns = deeper
    }
    
    overall_score = sum(scores.values()) / len(scores)
    
    return {
        "overall_score": round(overall_score, 1),
        "scores": scores,
        "num_citations": len(citations),
        "num_turns": stats["num_answers"],
        "quality_level": (
            "Excellent" if overall_score >= 8 else
            "Good" if overall_score >= 6 else
            "Fair" if overall_score >= 4 else
            "Poor"
        )
    }
