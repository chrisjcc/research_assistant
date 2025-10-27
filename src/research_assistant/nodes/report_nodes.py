"""Node functions for report generation and synthesis.

This module contains LangGraph node functions for transforming interview
findings into polished report sections and synthesizing them into a final
comprehensive report.

Example:
    >>> from research_assistant.nodes.report_nodes import write_section
    >>> result = write_section(state)
    >>> print(result['sections'][0][:100])
"""

import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..core.state import InterviewState, ResearchGraphState
from ..prompts.report_prompts import (
    format_conclusion_instructions,
    format_introduction_instructions,
    format_report_instructions,
    format_section_instructions,
)

# Configure logger
logger = logging.getLogger(__name__)


class ReportGenerationError(Exception):
    """Raised when report generation fails."""

    pass


def write_section(
    state: InterviewState, llm: Optional[ChatOpenAI] = None, detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Write a report section based on interview findings.

    This node transforms interview transcripts and context documents into
    a polished report section with proper structure, citations, and
    narrative flow.

    Args:
        state: Interview state with interview transcript and context.
        llm: Optional LLM instance.
        detailed_prompts: If True, use more detailed instructions.

    Returns:
        Dictionary with 'sections' containing the new section.

    Raises:
        ReportGenerationError: If section writing fails.
        ValueError: If required state fields are missing.

    Example:
        >>> state = {
        ...     "analyst": analyst_instance,
        ...     "interview": "Q: ... A: ...",
        ...     "context": ["<Document>...</Document>"]
        ... }
        >>> result = write_section(state)
    """
    logger.info("Writing report section")

    # Extract state
    interview = state.get("interview", "")
    context = state.get("context", [])
    analyst = state.get("analyst")

    # Validate state
    if not analyst:
        raise ValueError("Analyst is required in state")

    if not context:
        logger.warning("No context provided for section writing")

    logger.debug(
        f"Writing section for analyst: {analyst.name}, "
        f"context_docs={len(context)}, "
        f"interview_length={len(interview)}"
    )

    # Initialize LLM if needed
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Format context as a single string
    context_str = "\n\n".join(str(doc) for doc in context)

    # Format system message
    system_message_content = format_section_instructions(
        analyst_focus=analyst.description, context=context_str, detailed=detailed_prompts
    )

    # Create messages - use context as the primary source
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content=f"Use this source to write your section: {context_str}"),
    ]

    try:
        logger.info("Invoking LLM for section writing")
        section = llm.invoke(messages)

        section_content = section.content if hasattr(section, "content") else str(section)

        logger.debug(f"Generated section length: {len(section_content)} chars")
        logger.info("Successfully generated report section")

        return {"sections": [section_content]}

    except Exception as e:
        logger.error(f"Failed to write section: {str(e)}", exc_info=True)
        raise ReportGenerationError(f"Section writing failed: {str(e)}") from e


def write_report(
    state: ResearchGraphState, llm: Optional[ChatOpenAI] = None, detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Synthesize all sections into a unified report body.

    This node takes all analyst sections and weaves them together into
    a cohesive narrative with consolidated insights and sources.

    Args:
        state: Research state with sections and topic.
        llm: Optional LLM instance.
        detailed_prompts: If True, use more detailed instructions.

    Returns:
        Dictionary with 'content' containing the synthesized report.

    Raises:
        ReportGenerationError: If report synthesis fails.
        ValueError: If required state fields are missing.

    Example:
        >>> state = {
        ...     "topic": "AI Safety",
        ...     "sections": [section1, section2, section3]
        ... }
        >>> result = write_report(state)
    """
    logger.info("Synthesizing report from sections")

    # Extract state
    sections = state.get("sections", [])
    topic = state.get("topic")

    # Validate state
    if not topic:
        raise ValueError("Topic is required in state")

    if not sections:
        raise ValueError("No sections available for report synthesis")

    logger.debug(f"Synthesizing report: topic='{topic}', " f"num_sections={len(sections)}")

    # Initialize LLM if needed
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Concatenate all sections
    formatted_sections = "\n\n".join([f"{section}" for section in sections])

    logger.debug(f"Total sections content: {len(formatted_sections)} chars")

    # Format system message
    system_message_content = format_report_instructions(
        topic=topic, context=formatted_sections, detailed=detailed_prompts
    )

    # Create messages
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content="Write a report based upon these memos."),
    ]

    try:
        logger.info("Invoking LLM for report synthesis")
        report = llm.invoke(messages)

        report_content = report.content if hasattr(report, "content") else str(report)

        logger.debug(f"Generated report length: {len(report_content)} chars")
        logger.info("Successfully synthesized report")

        return {"content": report_content}

    except Exception as e:
        logger.error(f"Failed to write report: {str(e)}", exc_info=True)
        raise ReportGenerationError(f"Report synthesis failed: {str(e)}") from e


def write_introduction(
    state: ResearchGraphState, llm: Optional[ChatOpenAI] = None, detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Write the introduction for the final report.

    Creates an engaging introduction that previews the report's content
    and establishes context for the research topic.

    Args:
        state: Research state with sections and topic.
        llm: Optional LLM instance.
        detailed_prompts: If True, use more detailed instructions.

    Returns:
        Dictionary with 'introduction' containing the intro text.

    Raises:
        ReportGenerationError: If introduction writing fails.

    Example:
        >>> result = write_introduction(state)
        >>> print(result['introduction'][:100])
    """
    logger.info("Writing report introduction")

    # Extract state
    sections = state.get("sections", [])
    topic = state.get("topic")

    # Validate
    if not topic:
        raise ValueError("Topic is required in state")

    if not sections:
        logger.warning("No sections available for introduction context")

    logger.debug(f"Writing introduction for topic='{topic}'")

    # Initialize LLM if needed
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Format instructions
    instructions = format_introduction_instructions(
        topic=topic, sections=sections, detailed=detailed_prompts
    )

    # Create messages
    messages = [instructions, HumanMessage(content="Write the report introduction")]

    try:
        logger.info("Invoking LLM for introduction writing")
        intro = llm.invoke(messages)

        intro_content = intro.content if hasattr(intro, "content") else str(intro)

        logger.debug(f"Generated introduction length: {len(intro_content)} chars")
        logger.info("Successfully generated introduction")

        return {"introduction": intro_content}

    except Exception as e:
        logger.error(f"Failed to write introduction: {str(e)}", exc_info=True)
        raise ReportGenerationError(f"Introduction writing failed: {str(e)}") from e


def write_conclusion(
    state: ResearchGraphState, llm: Optional[ChatOpenAI] = None, detailed_prompts: bool = False
) -> Dict[str, Any]:
    """Write the conclusion for the final report.

    Creates a compelling conclusion that synthesizes key takeaways and
    provides forward-looking insights.

    Args:
        state: Research state with sections and topic.
        llm: Optional LLM instance.
        detailed_prompts: If True, use more detailed instructions.

    Returns:
        Dictionary with 'conclusion' containing the conclusion text.

    Raises:
        ReportGenerationError: If conclusion writing fails.

    Example:
        >>> result = write_conclusion(state)
        >>> print(result['conclusion'][:100])
    """
    logger.info("Writing report conclusion")

    # Extract state
    sections = state.get("sections", [])
    topic = state.get("topic")

    # Validate
    if not topic:
        raise ValueError("Topic is required in state")

    if not sections:
        logger.warning("No sections available for conclusion context")

    logger.debug(f"Writing conclusion for topic='{topic}'")

    # Initialize LLM if needed
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Format instructions
    instructions = format_conclusion_instructions(
        topic=topic, sections=sections, detailed=detailed_prompts
    )

    # Create messages
    messages = [instructions, HumanMessage(content="Write the report conclusion")]

    try:
        logger.info("Invoking LLM for conclusion writing")
        conclusion = llm.invoke(messages)

        conclusion_content = (
            conclusion.content if hasattr(conclusion, "content") else str(conclusion)
        )

        logger.debug(f"Generated conclusion length: {len(conclusion_content)} chars")
        logger.info("Successfully generated conclusion")

        return {"conclusion": conclusion_content}

    except Exception as e:
        logger.error(f"Failed to write conclusion: {str(e)}", exc_info=True)
        raise ReportGenerationError(f"Conclusion writing failed: {str(e)}") from e


def finalize_report(state: ResearchGraphState) -> Dict[str, Any]:
    """Assemble all report components into the final document.

    This is the final "reduce" step that combines the introduction,
    content, conclusion, and sources into a complete markdown report.

    Args:
        state: Research state with all report components.

    Returns:
        Dictionary with 'final_report' containing the complete report.

    Raises:
        ValueError: If required components are missing.

    Example:
        >>> result = finalize_report(state)
        >>> with open('report.md', 'w') as f:
        ...     f.write(result['final_report'])
    """
    logger.info("Finalizing report assembly")

    # Extract components
    introduction = state.get("introduction", "")
    content = state.get("content", "")
    conclusion = state.get("conclusion", "")

    # Validate required components
    if not introduction:
        raise ValueError("Introduction is missing")

    if not content:
        raise ValueError("Content is missing")

    if not conclusion:
        raise ValueError("Conclusion is missing")

    logger.debug(
        f"Assembling report: intro={len(introduction)} chars, "
        f"content={len(content)} chars, conclusion={len(conclusion)} chars"
    )

    # Clean up content
    # Remove "## Insights" header if present at the start
    content_cleaned = content
    if content_cleaned.startswith("## Insights"):
        content_cleaned = content_cleaned[len("## Insights") :].strip()

    # Extract sources from content if present
    sources = None
    if "## Sources" in content_cleaned:
        try:
            content_body, sources_section = content_cleaned.split("\n## Sources\n", 1)
            content_cleaned = content_body
            sources = sources_section
            logger.debug("Extracted sources section from content")
        except ValueError:
            # Multiple "## Sources" headers or other issue
            logger.warning("Could not cleanly extract sources section")

    # Assemble final report
    report_parts = [introduction.strip(), "---", content_cleaned.strip(), "---", conclusion.strip()]

    # Add sources if present
    if sources:
        report_parts.extend(["", "## Sources", sources.strip()])

    final_report = "\n\n".join(report_parts)

    logger.info(f"Final report assembled: {len(final_report)} chars total")

    return {"final_report": final_report}


# Report quality and utility functions


def extract_sources_from_content(content: str) -> List[str]:
    """Extract source citations from report content.

    Args:
        content: Report content with citations.

    Returns:
        List of source strings.

    Example:
        >>> sources = extract_sources_from_content(report_content)
        >>> print(f"Found {len(sources)} sources")
    """
    # Pattern to match source lines like "[1] Source text"
    pattern = r"^\[\d+\]\s+.+"

    sources = []
    in_sources_section = False

    for line in content.split("\n"):
        if "## Sources" in line or "### Sources" in line:
            in_sources_section = True
            continue

        if in_sources_section:
            if re.match(pattern, line.strip()):
                sources.append(line.strip())
            elif line.strip() and not line.startswith("["):
                # Hit non-source content, stop
                break

    return sources


def count_citations_in_content(content: str) -> int:
    """Count the number of inline citations in content.

    Args:
        content: Report content with citations like [1], [2,3], etc.

    Returns:
        Count of citation instances.

    Example:
        >>> count = count_citations_in_content(report)
        >>> print(f"{count} citations found")
    """
    pattern = r"\[\d+(?:,\s*\d+)*\]"
    matches = re.findall(pattern, content)
    return len(matches)


def get_report_statistics(state: ResearchGraphState) -> Dict[str, Any]:
    """Get comprehensive statistics about the generated report.

    Args:
        state: Research state with report components.

    Returns:
        Dictionary containing report statistics.

    Example:
        >>> stats = get_report_statistics(state)
        >>> print(f"Report has {stats['total_words']} words")
    """
    introduction = state.get("introduction", "")
    content = state.get("content", "")
    conclusion = state.get("conclusion", "")
    final_report = state.get("final_report", "")
    sections = state.get("sections", [])

    # Word counts
    intro_words = len(introduction.split())
    content_words = len(content.split())
    conclusion_words = len(conclusion.split())
    total_words = len(final_report.split()) if final_report else 0

    # Citation counts
    citations_count = count_citations_in_content(final_report if final_report else content)

    # Source extraction
    sources = extract_sources_from_content(final_report if final_report else content)

    return {
        "num_sections": len(sections),
        "intro_words": intro_words,
        "content_words": content_words,
        "conclusion_words": conclusion_words,
        "total_words": total_words,
        "total_chars": len(final_report) if final_report else 0,
        "num_citations": citations_count,
        "num_sources": len(sources),
        "is_complete": bool(final_report),
    }


def format_report_summary(state: ResearchGraphState) -> str:
    """Format a human-readable summary of the report.

    Args:
        state: Research state to summarize.

    Returns:
        Formatted summary string.

    Example:
        >>> summary = format_report_summary(state)
        >>> print(summary)
    """
    stats = get_report_statistics(state)
    topic = state.get("topic", "Unknown")
    analysts = state.get("analysts", [])

    lines = [
        f"Research Report Summary",
        "=" * 50,
        f"Topic: {topic}",
        f"Analysts: {len(analysts)}",
        f"Sections: {stats['num_sections']}",
        "",
        "Word Counts:",
        f"  Introduction: {stats['intro_words']} words",
        f"  Main Content: {stats['content_words']} words",
        f"  Conclusion: {stats['conclusion_words']} words",
        f"  Total: {stats['total_words']} words",
        "",
        f"Citations: {stats['num_citations']}",
        f"Unique Sources: {stats['num_sources']}",
        "",
        f"Status: {'Complete' if stats['is_complete'] else 'In Progress'}",
    ]

    return "\n".join(lines)


def validate_report_structure(content: str) -> Dict[str, bool]:
    """Validate that report content follows expected structure.

    Args:
        content: Report content to validate.

    Returns:
        Dictionary with validation results for different aspects.

    Example:
        >>> validation = validate_report_structure(final_report)
        >>> if not validation['has_sources']:
        ...     print("Warning: No sources section found")
    """
    return {
        "has_title": bool(re.search(r"^#\s+.+", content, re.MULTILINE)),
        "has_introduction": "## Introduction" in content or "## introduction" in content,
        "has_conclusion": "## Conclusion" in content or "## conclusion" in content,
        "has_sources": "## Sources" in content or "### Sources" in content,
        "has_citations": bool(re.search(r"\[\d+\]", content)),
        "proper_markdown": content.count("#") >= 2,  # At least some headers
    }


def assess_report_quality(state: ResearchGraphState) -> Dict[str, Any]:
    """Assess overall quality of the generated report.

    Provides quality metrics based on various heuristics.

    Args:
        state: Completed research state.

    Returns:
        Dictionary containing quality assessment.

    Example:
        >>> quality = assess_report_quality(state)
        >>> print(f"Quality: {quality['quality_level']}")
    """
    stats = get_report_statistics(state)
    final_report = state.get("final_report", "")
    validation = validate_report_structure(final_report) if final_report else {}

    # Calculate scores
    scores = {
        "completeness": (
            10
            if validation.get("has_introduction")
            and validation.get("has_conclusion")
            and validation.get("has_sources")
            else 5
        ),
        "length": min(10, stats["total_words"] / 100),  # Target ~1000 words
        "citation_density": min(10, stats["num_citations"] / 2),  # More citations better
        "structure": sum(validation.values()) * 10 / len(validation) if validation else 0,
    }

    overall_score = sum(scores.values()) / len(scores)

    return {
        "overall_score": round(overall_score, 1),
        "scores": scores,
        "validation": validation,
        "quality_level": (
            "Excellent"
            if overall_score >= 8
            else "Good" if overall_score >= 6 else "Fair" if overall_score >= 4 else "Poor"
        ),
        "recommendations": _generate_recommendations(stats, validation),
    }


def _generate_recommendations(stats: Dict[str, Any], validation: Dict[str, bool]) -> List[str]:
    """Generate improvement recommendations based on statistics.

    Args:
        stats: Report statistics.
        validation: Validation results.

    Returns:
        List of recommendation strings.
    """
    recommendations = []

    if stats["total_words"] < 500:
        recommendations.append("Report is quite short; consider more detailed analysis")

    if stats["num_citations"] < 5:
        recommendations.append("Few citations; ensure all claims are properly sourced")

    if not validation.get("has_sources"):
        recommendations.append("Missing sources section; add comprehensive source list")

    if stats["num_sources"] < 3:
        recommendations.append("Limited sources; consider broader research base")

    if not validation.get("has_introduction"):
        recommendations.append("Missing introduction; add context and overview")

    if not validation.get("has_conclusion"):
        recommendations.append("Missing conclusion; add synthesis and takeaways")

    return recommendations if recommendations else ["Report meets quality standards"]
