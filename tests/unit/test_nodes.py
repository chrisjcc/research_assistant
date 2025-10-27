"""Unit tests for node functions.

Tests individual node functions with mocked dependencies.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from research_assistant.nodes.analyst_nodes import (
    create_analysts,
    format_analysts_for_review,
    get_analyst_diversity_metrics,
    human_feedback,
    validate_analyst_feedback,
)
from research_assistant.nodes.interview_nodes import (
    generate_answer,
    generate_question,
    get_interview_statistics,
    route_messages,
    save_interview,
)
from research_assistant.nodes.report_nodes import (
    finalize_report,
    write_conclusion,
    write_introduction,
    write_report,
    write_section,
)

# ============================================================================
# Analyst Node Tests
# ============================================================================


class TestAnalystNodes:
    """Test suite for analyst node functions."""

    def test_create_analysts_success(self, sample_generate_analysts_state, mock_llm):
        """Test expert specializing in comprehensive testing."""
        result = create_analysts(sample_generate_analysts_state, llm=mock_llm)

        assert "analysts" in result
        assert len(result["analysts"]) > 0
        assert mock_llm.with_structured_output.called

    def test_create_analysts_missing_topic(self, mock_llm):
        """Test analyst creation with missing topic."""
        state = {"max_analysts": 3, "human_analyst_feedback": ""}

        with pytest.raises(ValueError, match="Topic is required"):
            create_analysts(state, llm=mock_llm)

    def test_create_analysts_invalid_max_analysts(self, mock_llm):
        """Test analyst creation with invalid max_analysts."""
        state = {"topic": "AI Safety", "max_analysts": 0, "human_analyst_feedback": ""}  # Invalid

        with pytest.raises(ValueError, match="max_analysts is required"):
            create_analysts(state, llm=mock_llm)

    def test_create_analysts_with_feedback(self, sample_generate_analysts_state, mock_llm):
        """Test analyst creation with human feedback."""
        sample_generate_analysts_state["human_analyst_feedback"] = "Need more technical experts"

        result = create_analysts(sample_generate_analysts_state, llm=mock_llm)

        assert "analysts" in result
        assert mock_llm.with_structured_output.called

    def test_human_feedback_node(self, sample_generate_analysts_state):
        """Test human feedback node (no-op)."""
        result = human_feedback(sample_generate_analysts_state)

        assert result == {}

    def test_validate_analyst_feedback_approve(self):
        """Test feedback validation with approval."""
        assert validate_analyst_feedback("approve") is True
        assert validate_analyst_feedback("APPROVE") is True
        assert validate_analyst_feedback("  approve  ") is True

    def test_validate_analyst_feedback_reject(self):
        """Test feedback validation with rejection."""
        assert validate_analyst_feedback("Need changes") is False
        assert validate_analyst_feedback("Regenerate") is False

    def test_validate_analyst_feedback_empty(self):
        """Test feedback validation with empty string."""
        assert validate_analyst_feedback("") is True
        assert validate_analyst_feedback(None) is True

    def test_format_analysts_for_review(self, sample_analysts):
        """Test formatting analysts for human review."""
        formatted = format_analysts_for_review(sample_analysts)

        assert "ANALYST TEAM" in formatted
        assert "Dr. Alice Smith" in formatted
        assert "Prof. Bob Johnson" in formatted
        assert str(len(sample_analysts)) in formatted

    def test_format_analysts_for_review_empty(self):
        """Test formatting empty analyst list."""
        formatted = format_analysts_for_review([])

        assert "No analysts" in formatted

    def test_get_analyst_diversity_metrics(self, sample_analysts):
        """Test calculating diversity metrics."""
        metrics = get_analyst_diversity_metrics(sample_analysts)

        assert metrics["total_analysts"] == 3
        assert metrics["unique_roles"] == 3
        assert metrics["unique_affiliations"] == 3
        assert metrics["role_diversity_ratio"] == 1.0
        assert metrics["affiliation_diversity_ratio"] == 1.0

    def test_get_analyst_diversity_metrics_empty(self):
        """Test diversity metrics with empty list."""
        metrics = get_analyst_diversity_metrics([])

        assert metrics["total_analysts"] == 0
        assert metrics["unique_roles"] == 0


# ============================================================================
# Interview Node Tests
# ============================================================================


class TestInterviewNodes:
    """Test suite for interview node functions."""

    def test_generate_question_success(self, sample_interview_state, mock_llm):
        """Test successful question generation."""
        result = generate_question(sample_interview_state, llm=mock_llm)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert mock_llm.invoke.called

    def test_generate_question_missing_analyst(self, mock_llm):
        """Test question generation without analyst."""
        state = {"messages": []}

        with pytest.raises(ValueError, match="Analyst is required"):
            generate_question(state, llm=mock_llm)

    def test_generate_answer_success(self, sample_interview_state, mock_llm):
        """Test successful answer generation."""
        sample_interview_state["context"] = ["Test context"]

        result = generate_answer(sample_interview_state, llm=mock_llm)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].name == "expert"

    def test_generate_answer_no_context(self, sample_interview_state, mock_llm):
        """Test answer generation without context."""
        sample_interview_state["context"] = []

        # Should still work, just with empty context
        result = generate_answer(sample_interview_state, llm=mock_llm)

        assert "messages" in result
        assert mock_llm.invoke.called

    def test_save_interview(self, sample_interview_state):
        """Test saving interview transcript."""
        result = save_interview(sample_interview_state)

        assert "interview" in result
        assert len(result["interview"]) > 0
        assert isinstance(result["interview"], str)

    def test_save_interview_empty_messages(self):
        """Test saving interview with no messages."""
        state = {"messages": []}

        result = save_interview(state)

        assert result["interview"] == ""

    def test_route_messages_continue(self, sample_interview_state):
        """Test message routing to continue interview."""
        from langchain_core.messages import AIMessage, HumanMessage

        sample_interview_state["max_num_turns"] = 2

        # Only 1 expert response, should continue
        sample_interview_state["messages"] = [
            HumanMessage(content="Let's discuss AI safety"),
            AIMessage(content="I'd be happy to discuss AI safety", name="expert"),
        ]

        route = route_messages(sample_interview_state)

        assert route == "ask_question"

    def test_route_messages_end_max_turns(self, sample_interview_state):
        """Test message routing when max turns reached."""
        sample_interview_state["max_num_turns"] = 1

        # Already 1 expert response, should end
        route = route_messages(sample_interview_state)

        assert route == "save_interview"

    def test_route_messages_conclusion(self, sample_interview_state):
        """Test message routing when analyst concludes."""
        from langchain_core.messages import HumanMessage

        # Add conclusion message
        sample_interview_state["messages"].append(
            HumanMessage(content="Thank you so much for your help!")
        )

        route = route_messages(sample_interview_state)

        assert route == "save_interview"

    def test_get_interview_statistics(self, sample_interview_state):
        """Test getting interview statistics."""
        sample_interview_state["context"] = ["doc1", "doc2"]

        stats = get_interview_statistics(sample_interview_state)

        assert "analyst_name" in stats
        assert "num_questions" in stats
        assert "num_answers" in stats
        assert stats["num_context_docs"] == 2


# ============================================================================
# Report Node Tests
# ============================================================================


class TestReportNodes:
    """Test suite for report node functions."""

    def test_write_section_success(self, sample_interview_state, mock_llm):
        """Test successful section writing."""
        sample_interview_state["interview"] = "Q: Test? A: Answer [1]"
        sample_interview_state["context_docs"] = ["Test context"]

        result = write_section(sample_interview_state, llm=mock_llm)

        assert "sections" in result
        assert len(result["sections"]) == 1
        assert mock_llm.invoke.called

    def test_write_section_missing_analyst(self, mock_llm):
        """Test section writing without analyst."""
        state = {"interview": "", "context": []}

        with pytest.raises(ValueError, match="Analyst is required"):
            write_section(state, llm=mock_llm)

    def test_write_report_success(self, sample_research_state, mock_llm):
        """Test successful report synthesis."""
        sample_research_state["sections"] = ["## Section 1\nContent 1", "## Section 2\nContent 2"]

        result = write_report(sample_research_state, llm=mock_llm)

        assert "content" in result
        assert len(result["content"]) > 0
        assert mock_llm.invoke.called

    def test_write_report_no_sections(self, mock_llm):
        """Test report writing with no sections."""
        state = {"topic": "Test", "sections": []}

        with pytest.raises(ValueError, match="No sections"):
            write_report(state, llm=mock_llm)

    def test_write_introduction_success(self, sample_research_state, mock_llm):
        """Test introduction writing."""
        sample_research_state["sections"] = ["## Section 1\nContent"]

        result = write_introduction(sample_research_state, llm=mock_llm)

        assert "introduction" in result
        assert len(result["introduction"]) > 0

    def test_write_conclusion_success(self, sample_research_state, mock_llm):
        """Test conclusion writing."""
        sample_research_state["sections"] = ["## Section 1\nContent"]

        result = write_conclusion(sample_research_state, llm=mock_llm)

        assert "conclusion" in result
        assert len(result["conclusion"]) > 0

    def test_finalize_report_success(self, sample_research_state):
        """Test final report assembly."""
        sample_research_state["introduction"] = "# Title\n## Introduction\nIntro text"
        sample_research_state["content"] = "## Insights\nContent text\n## Sources\n[1] Source"
        sample_research_state["conclusion"] = "## Conclusion\nConclusion text"

        result = finalize_report(sample_research_state)

        assert "final_report" in result
        assert "Title" in result["final_report"]
        assert "Introduction" in result["final_report"]
        assert "Conclusion" in result["final_report"]
        assert "Sources" in result["final_report"]

    def test_finalize_report_missing_components(self):
        """Test finalization with missing components."""
        state = {"introduction": "", "content": "", "conclusion": ""}

        with pytest.raises(ValueError):
            finalize_report(state)

    def test_finalize_report_strips_insights_header(self):
        """Test that ## Insights header is stripped."""
        state = {
            "introduction": "# Title\n## Introduction\nIntro",
            "content": "## Insights\nContent here",
            "conclusion": "## Conclusion\nConclusion",
        }

        result = finalize_report(state)

        # Insights header should be removed from content
        assert (
            "## Insights"
            not in result["final_report"].split("Introduction")[1].split("Conclusion")[0]
        )


# ============================================================================
# Node Error Handling Tests
# ============================================================================


class TestNodeErrorHandling:
    """Test error handling in node functions."""

    def test_create_analysts_llm_failure(self, sample_generate_analysts_state, mock_failing_llm):
        """Test analyst creation when LLM fails."""
        from research_assistant.nodes.analyst_nodes import AnalystCreationError

        with pytest.raises(AnalystCreationError):
            create_analysts(sample_generate_analysts_state, llm=mock_failing_llm)

    def test_generate_question_llm_failure(self, sample_interview_state, mock_failing_llm):
        """Test question generation when LLM fails."""
        from research_assistant.nodes.interview_nodes import InterviewError

        with pytest.raises(InterviewError):
            generate_question(sample_interview_state, llm=mock_failing_llm)

    def test_write_report_llm_failure(self, sample_research_state, mock_failing_llm):
        """Test report writing when LLM fails."""
        from research_assistant.nodes.report_nodes import ReportGenerationError

        sample_research_state["sections"] = ["Content"]

        with pytest.raises(ReportGenerationError):
            write_report(sample_research_state, llm=mock_failing_llm)


# ============================================================================
# Node Integration Tests (Light)
# ============================================================================


class TestNodeIntegration:
    """Light integration tests for node interactions."""

    def test_interview_question_answer_flow(self, sample_interview_state, mock_llm):
        """Test question-answer flow."""
        # Generate question
        q_result = generate_question(sample_interview_state, llm=mock_llm)
        sample_interview_state["messages"].extend(q_result["messages"])

        # Add context
        sample_interview_state["context"] = ["Test context"]

        # Generate answer
        a_result = generate_answer(sample_interview_state, llm=mock_llm)
        sample_interview_state["messages"].extend(a_result["messages"])

        # Save interview
        save_result = save_interview(sample_interview_state)

        assert len(save_result["interview"]) > 0

    def test_report_assembly_flow(self, sample_research_state, mock_llm):
        """Test complete report assembly."""
        # Add sections
        sample_research_state["sections"] = [
            "## Section 1\nContent [1]",
            "## Section 2\nContent [2]",
        ]

        # Write components
        intro_result = write_introduction(sample_research_state, llm=mock_llm)
        content_result = write_report(sample_research_state, llm=mock_llm)
        conclusion_result = write_conclusion(sample_research_state, llm=mock_llm)

        # Update state
        sample_research_state.update(intro_result)
        sample_research_state.update(content_result)
        sample_research_state.update(conclusion_result)

        # Finalize
        final_result = finalize_report(sample_research_state)

        assert "final_report" in final_result
        assert len(final_result["final_report"]) > 0


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.parametrize(
    "max_analysts,expected_valid",
    [
        (1, True),
        (3, True),
        (10, True),
        (0, False),
        (11, False),
        (-1, False),
    ],
)
def test_max_analysts_validation(max_analysts, expected_valid, mock_llm):
    """Test max_analysts parameter validation."""
    state = {"topic": "Test", "max_analysts": max_analysts, "human_analyst_feedback": ""}

    if expected_valid:
        result = create_analysts(state, llm=mock_llm)
        assert "analysts" in result
    else:
        with pytest.raises(ValueError):
            create_analysts(state, llm=mock_llm)


@pytest.mark.parametrize(
    "feedback,should_approve",
    [
        ("approve", True),
        ("APPROVE", True),
        ("Approve", True),
        ("  approve  ", True),
        ("", True),
        ("reject", False),
        ("need changes", False),
        ("more technical", False),
    ],
)
def test_feedback_validation_cases(feedback, should_approve):
    """Test various feedback validation cases."""
    result = validate_analyst_feedback(feedback)
    assert result == should_approve
