"""Pytest configuration and shared fixtures.

This module provides reusable fixtures for testing the research assistant,
including mock LLMs, sample data, and configuration objects.

Example:
    >>> def test_something(mock_llm, sample_analyst):
    ...     result = function_under_test(mock_llm, sample_analyst)
    ...     assert result is not None
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from omegaconf import DictConfig, OmegaConf

from research_assistant.core.schemas import Analyst, Perspectives, SearchQuery

# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_config() -> DictConfig:
    """Provide test configuration.

    Returns:
        Test configuration with minimal settings.
    """
    return OmegaConf.create(
        {
            "llm": {
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.0,
                "max_tokens": 1000,
            },
            "search": {
                "web": {
                    "enabled": True,
                    "max_results": 2,
                    "use_cache": False,
                },
                "wikipedia": {
                    "enabled": True,
                    "load_max_docs": 1,
                    "use_cache": False,
                },
            },
            "research": {
                "max_analysts": 2,
                "max_interview_turns": 1,
                "enable_interrupts": False,
                "detailed_prompts": False,
            },
            "logging": {
                "level": "ERROR",  # Quiet during tests
                "console": False,
            },
        }
    )


@pytest.fixture
def minimal_config() -> dict[str, Any]:
    """Provide minimal configuration dictionary.

    Returns:
        Minimal configuration for testing.
    """
    return {"max_analysts": 2, "max_interview_turns": 1, "topic": "Test Topic"}


# ============================================================================
# Mock LLM Fixtures
# ============================================================================


@pytest.fixture
def mock_llm():
    """Provide a mock LLM that returns predefined responses.

    Returns:
        Mock LLM instance with proper stop conditions for interview flow.
    """
    mock = Mock()

    # ✅ FIX: Use mock attribute to track calls (resets per test)
    mock._call_count = 0

    def mock_invoke(messages):
        """Mock invoke that simulates realistic interview responses."""
        # Increment counter on the mock object itself
        mock._call_count += 1

        # After 3 calls, return conclusion message to stop interview
        if mock._call_count >= 3:
            return AIMessage(
                content="Thank you so much for your help! That's all I needed to know.",
                name=None,  # No name = interviewer concluding
            )

        # Check context to determine if this is question or answer generation
        if messages:
            last_msg = messages[-1] if isinstance(messages, list) else messages
            last_content = getattr(last_msg, "content", str(last_msg))

            # If there's search context, this is answer generation
            if "Document" in last_content or len(messages) > 2:
                return AIMessage(
                    content="Based on the research, here is my expert analysis [1].",
                    name="expert",  # Expert answering
                )

        # Default: question generation
        return AIMessage(
            content="That's an interesting question.\
            Can you tell me more about the specific aspects?",
            name=None,  # Interviewer asking
        )

    mock.invoke.side_effect = mock_invoke

    # Support structured output
    def with_structured_output(schema):
        structured_mock = Mock()

        # Return appropriate type based on schema
        if schema.__name__ == "Perspectives":
            structured_mock.invoke.return_value = Perspectives(
                analysts=[
                    Analyst(
                        name="Dr. Test",
                        role="Researcher",
                        affiliation="Test University",
                        description="Test expert specializing in comprehensive testing",
                    )
                ]
            )
        elif schema.__name__ == "SearchQuery":
            structured_mock.invoke.return_value = SearchQuery(search_query="test query")
        else:
            structured_mock.invoke.return_value = schema()

        return structured_mock

    # Make with_structured_output a Mock that wraps the function
    mock.with_structured_output = Mock(side_effect=with_structured_output)

    return mock


@pytest.fixture
def mock_llm_with_custom_response():
    """Factory fixture for creating mock LLM with custom responses.

    Returns:
        Function that creates mock LLM with specified response.

    Example:
        >>> llm = mock_llm_with_custom_response("Custom answer")
        >>> result = llm.invoke([])
        >>> assert result.content == "Custom answer"
    """

    def _create_mock(response_content: str = "Test response"):
        mock = Mock()
        mock.invoke.return_value = AIMessage(content=response_content)
        return mock

    return _create_mock


@pytest.fixture
def mock_failing_llm():
    """Provide a mock LLM that raises errors.

    Returns:
        Mock LLM that raises exceptions.
    """
    mock = Mock()
    mock.invoke.side_effect = Exception("LLM API Error")
    return mock


# ============================================================================
# Sample Data Fixtures - Analysts
# ============================================================================


@pytest.fixture
def sample_analyst() -> Analyst:
    """Provide a sample analyst instance.

    Returns:
        Sample Analyst object.
    """
    return Analyst(
        name="Dr. Alice Smith",
        role="AI Researcher",
        affiliation="MIT",
        description="Expert in machine learning and AI safety research",
    )


@pytest.fixture
def sample_analysts() -> list[Analyst]:
    """Provide a list of sample analysts.

    Returns:
        List of Analyst objects.
    """
    return [
        Analyst(
            name="Dr. Alice Smith",
            role="AI Researcher",
            affiliation="MIT",
            description="Expert in machine learning and AI safety",
        ),
        Analyst(
            name="Prof. Bob Johnson",
            role="Policy Analyst",
            affiliation="Stanford",
            description="Specializes in AI policy and ethics",
        ),
        Analyst(
            name="Dr. Carol Williams",
            role="Industry Practitioner",
            affiliation="Google",
            description="Focuses on practical AI deployment",
        ),
    ]


@pytest.fixture
def sample_perspectives(sample_analysts) -> Perspectives:
    """Provide a sample Perspectives instance.

    Returns:
        Perspectives object with sample analysts.
    """
    return Perspectives(analysts=sample_analysts)


# ============================================================================
# Sample Data Fixtures - Messages
# ============================================================================


@pytest.fixture
def sample_messages() -> list[Any]:
    """Provide sample conversation messages.

    Returns:
        List of message objects.
    """
    return [
        HumanMessage(content="Let's discuss AI safety"),
        AIMessage(content="I'd be happy to discuss AI safety", name="expert"),
        HumanMessage(content="What are the main concerns?"),
        AIMessage(
            content="Main concerns include alignment, robustness, and transparency [1]",
            name="expert",
        ),
    ]


@pytest.fixture
def sample_system_message() -> SystemMessage:
    """Provide a sample system message.

    Returns:
        SystemMessage object.
    """
    return SystemMessage(content="You are a helpful research assistant.")


# ============================================================================
# Sample Data Fixtures - Search Results
# ============================================================================


@pytest.fixture
def sample_search_results() -> list[dict[str, Any]]:
    """Provide sample search results.

    Returns:
        List of search result dictionaries.
    """
    return [
        {
            "url": "https://example.com/article1",
            "content": "This is the content of the first article about AI safety.",
        },
        {
            "url": "https://example.com/article2",
            "content": "This article discusses machine learning best practices.",
        },
    ]


@pytest.fixture
def sample_formatted_context() -> str:
    """Provide sample formatted context from search.

    Returns:
        Formatted context string.
    """
    return """<Document href="https://example.com/article1"/>
This is the content of the first article about AI safety.
</Document>

---

<Document href="https://example.com/article2"/>
This article discusses machine learning best practices.
</Document>"""


# ============================================================================
# Sample Data Fixtures - State Objects
# ============================================================================


@pytest.fixture
def sample_interview_state(sample_analyst, sample_messages) -> dict[str, Any]:
    """Provide sample InterviewState.

    Returns:
        InterviewState dictionary.
    """
    return {
        "analyst": sample_analyst,
        "messages": sample_messages,
        "max_num_turns": 3,
        "context": [],
        "interview": "",
        "sections": [],
    }


@pytest.fixture
def sample_research_state(sample_analysts) -> dict[str, Any]:
    """Provide sample ResearchGraphState.

    Returns:
        ResearchGraphState dictionary.
    """
    return {
        "topic": "AI Safety",
        "max_analysts": 3,
        "human_analyst_feedback": "approve",
        "analysts": sample_analysts,
        "sections": [],
        "introduction": "",
        "content": "",
        "conclusion": "",
        "final_report": "",
    }


@pytest.fixture
def sample_generate_analysts_state() -> dict[str, Any]:
    """Provide sample GenerateAnalystsState.

    This state is used for the analyst generation phase of the workflow.

    Returns:
        GenerateAnalystsState dictionary.
    """
    return {"topic": "AI Safety", "max_analysts": 3, "human_analyst_feedback": "", "analysts": []}


# ============================================================================
# Mock Search Tool Fixtures
# ============================================================================


@pytest.fixture
def mock_web_search():
    """Provide mock web search tool.

    Returns:
        Mock WebSearchTool instance.
    """
    mock = Mock()
    mock.search.return_value = [
        {"url": "https://example.com/result1", "content": "Search result content 1"}
    ]
    mock.format_results.return_value = "<Document>Formatted results</Document>"
    return mock


@pytest.fixture
def mock_wikipedia_search():
    """Provide mock Wikipedia search tool.

    Returns:
        Mock WikipediaSearchTool instance.
    """
    mock = Mock()

    # Mock document
    mock_doc = Mock()
    mock_doc.page_content = "Wikipedia article content"
    mock_doc.metadata = {"source": "wikipedia", "page": "Test"}

    mock.search.return_value = [mock_doc]
    mock.format_results.return_value = "<Document>Formatted Wikipedia</Document>"

    return mock


@pytest.fixture
def mock_search_query_generator():
    """Provide mock search query generator.

    Returns:
        Mock SearchQueryGenerator instance.
    """
    mock = Mock()
    mock.generate_from_messages.return_value = SearchQuery(search_query="generated test query")
    return mock


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide temporary output directory.

    Args:
        tmp_path: Pytest's tmp_path fixture.

    Returns:
        Path to temporary directory.
    """
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_report_file(tmp_path) -> Path:
    """Provide sample report file.

    Args:
        tmp_path: Pytest's tmp_path fixture.

    Returns:
        Path to sample report file.
    """
    report_path = tmp_path / "sample_report.md"
    report_path.write_text("# Sample Report\n\nThis is a test report.")
    return report_path


# ============================================================================
# Graph Component Fixtures
# ============================================================================


@pytest.fixture
def mock_interview_graph():
    """Provide mock interview graph.

    Returns:
        Mock compiled interview graph that returns complete InterviewState.
    """
    mock = Mock()

    # FIXED: Return complete InterviewState dictionary, not just sections
    def mock_invoke(state):
        """Mock invoke that returns complete state."""
        return {
            "analyst": state.get("analyst"),
            "messages": state.get("messages", [])
            + [AIMessage(content="Mock expert response", name="expert")],
            "max_num_turns": state.get("max_num_turns", 0),
            "context": state.get("context", []) + ["<Document>Mock context</Document>"],
            "interview": "Mock interview transcript:\nQ: Question\nA: Answer",
            "sections": ["## Test Section\n\nTest content [1]\n\n### Sources\n[1] example.com"],
        }

    mock.invoke.side_effect = mock_invoke
    mock.side_effect = mock_invoke
    return mock


@pytest.fixture
def mock_research_graph():
    """Provide mock research graph.

    Returns:
        Mock compiled research graph.
    """
    mock = Mock()
    mock.invoke.return_value = {"final_report": "# Test Report\n\nFinal report content"}
    return mock


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def sample_metrics() -> dict[str, Any]:
    """Provide sample metrics dictionary.

    Returns:
        Dictionary with sample metrics.
    """
    return {
        "api_calls": 5,
        "total_tokens": 1500,
        "node_executions": {"test_node": [{"duration": 1.5, "tokens_used": 300, "api_calls": 1}]},
        "errors": [],
        "total_runtime": 10.5,
    }


@pytest.fixture(autouse=True)
def reset_metrics():
    """Automatically reset metrics before each test.

    This fixture runs before every test to ensure clean state.
    """
    from research_assistant.utils.logging import reset_metrics

    reset_metrics()
    yield
    reset_metrics()


@pytest.fixture
def mock_cache():
    """Provide mock cache implementation.

    Returns:
        Mock cache with get/set/delete methods.
    """
    cache_data = {}

    mock = Mock()
    mock.get.side_effect = lambda key: cache_data.get(key)
    mock.set.side_effect = lambda key, value: cache_data.update({key: value})
    mock.delete.side_effect = lambda key: cache_data.pop(key, None)
    mock.clear.side_effect = lambda: cache_data.clear()

    return mock


# ============================================================================
# VCR Fixtures (for recording/replaying API calls)
# ============================================================================


@pytest.fixture(scope="module")
def vcr_config():
    """Provide VCR configuration for recording API calls.

    Returns:
        Dictionary with VCR configuration.
    """
    return {
        "filter_headers": ["authorization", "api-key"],
        "record_mode": "once",  # Record once, then replay
        "match_on": ["uri", "method"],
        "cassette_library_dir": "tests/cassettes",
    }


@pytest.fixture
def vcr_cassette_name(request):
    """Generate VCR cassette name from test name.

    Args:
        request: Pytest request fixture.

    Returns:
        Cassette name for the current test.
    """
    return f"{request.node.name}.yaml"


# ============================================================================
# Parametrize Helpers
# ============================================================================


@pytest.fixture
def analyst_test_cases():
    """Provide test cases for analyst validation.

    Returns:
        List of (analyst_data, expected_valid) tuples.
    """
    return [
        # Valid cases
        (
            {
                "name": "Dr. Test",
                "role": "Researcher",
                "affiliation": "University",
                "description": "Test expert specializing in comprehensive testing",
            },
            True,
        ),
        # Invalid cases
        ({"name": "", "role": "R", "affiliation": "U", "description": "D"}, False),
        ({"name": "Test", "role": "", "affiliation": "U", "description": "D"}, False),
    ]


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers.

    Args:
        config: Pytest config object.
    """
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_api: mark test as requiring external API")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests.

    This runs once per test session.
    """
    # Set test mode environment variable
    import os

    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "ERROR"

    yield

    # Cleanup
    os.environ.pop("TESTING", None)
    os.environ.pop("LOG_LEVEL", None)
