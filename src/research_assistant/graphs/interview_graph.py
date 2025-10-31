"""Interview subgraph construction and management.

This module builds the interview subgraph that manages the conversation between
an analyst and an expert, including search, question generation, and answer
generation.

Example:
    >>> from research_assistant.graphs.interview_graph import build_interview_graph
    >>> interview_graph = build_interview_graph()
    >>> result = interview_graph.invoke(initial_state)
"""

import logging
from typing import Any, cast

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from ..core.state import InterviewState
from ..nodes.interview_nodes import (
    generate_answer,
    generate_question,
    route_messages,
    save_interview,
)
from ..nodes.report_nodes import write_section
from ..tools.search import SearchQueryGenerator, WebSearchTool, WikipediaSearchTool

# Configure logger
logger = logging.getLogger(__name__)


def search_web_node(
    state: InterviewState,
    search_tool: WebSearchTool | None = None,
    query_generator: SearchQueryGenerator | None = None,
) -> dict[str, Any]:
    """Node to execute web search based on conversation context.

    This node generates a search query from the conversation and retrieves
    relevant documents from the web.

    Args:
        state: Current interview state with messages.
        search_tool: Optional WebSearchTool instance.
        query_generator: Optional SearchQueryGenerator instance.

    Returns:
        Dictionary with 'context' containing formatted search results.

    Example:
        >>> result = search_web_node(state)
        >>> print(len(result['context']))
    """
    logger.info("Executing web search node")

    # Initialize tools if not provided
    if search_tool is None:
        search_tool = WebSearchTool(max_results=3)

    if query_generator is None:
        query_generator = SearchQueryGenerator()

    # Get messages from state
    messages = state.get("messages", [])

    if not messages:
        logger.warning("No messages in state for search query generation")
        return {"context": []}

    try:
        # Generate search query
        search_query = query_generator.generate_from_messages(messages)

        if not search_query.search_query:
            logger.warning("Empty search query generated")
            return {"context": []}

        logger.info(f"Generated query: {search_query.search_query}")

        # Execute search
        search_results = search_tool.search(search_query.search_query)

        # Format results
        formatted_results = search_tool.format_results(search_results)

        logger.info(f"Web search completed: {len(search_results)} results")

        return {"context": [formatted_results]}

    except Exception as e:
        logger.error(f"Web search failed: {str(e)}", exc_info=True)
        # Return empty context rather than failing the interview
        return {"context": []}


def search_wikipedia_node(
    state: InterviewState,
    search_tool: WikipediaSearchTool | None = None,
    query_generator: SearchQueryGenerator | None = None,
) -> dict[str, Any]:
    """Node to execute Wikipedia search based on conversation context.

    This node generates a search query from the conversation and retrieves
    relevant Wikipedia articles.

    Args:
        state: Current interview state with messages.
        search_tool: Optional WikipediaSearchTool instance.
        query_generator: Optional SearchQueryGenerator instance.

    Returns:
        Dictionary with 'context' containing formatted Wikipedia documents.

    Example:
        >>> result = search_wikipedia_node(state)
        >>> print(len(result['context']))
    """
    logger.info("Executing Wikipedia search node")

    # Initialize tools if not provided
    if search_tool is None:
        search_tool = WikipediaSearchTool(load_max_docs=2)

    if query_generator is None:
        query_generator = SearchQueryGenerator()

    # Get messages from state
    messages = state.get("messages", [])

    if not messages:
        logger.warning("No messages in state for search query generation")
        return {"context": []}

    try:
        # Generate search query
        search_query = query_generator.generate_from_messages(messages)

        if not search_query.search_query:
            logger.warning("Empty search query generated")
            return {"context": []}

        logger.info(f"Generated query: {search_query.search_query}")

        # Execute search
        documents = search_tool.search(search_query.search_query)

        # Format results
        formatted_results = search_tool.format_results(documents)

        logger.info(f"Wikipedia search completed: {len(documents)} documents")

        return {"context": [formatted_results]}

    except Exception as e:
        logger.error(f"Wikipedia search failed: {str(e)}", exc_info=True)
        # Return empty context rather than failing the interview
        return {"context": []}


def build_interview_graph(
    llm: ChatOpenAI | None = None,
    web_search_tool: WebSearchTool | None = None,
    wiki_search_tool: WikipediaSearchTool | None = None,
    query_generator: SearchQueryGenerator | None = None,
    detailed_prompts: bool = False,
) -> CompiledStateGraph[InterviewState, None, InterviewState, InterviewState]:
    """Build the interview subgraph.

    Creates a compiled graph that manages the interview process between an
    analyst and expert, including question generation, search, and answer
    generation.

    Args:
        llm: Optional LLM instance for all nodes.
        web_search_tool: Optional web search tool instance.
        wiki_search_tool: Optional Wikipedia search tool instance.
        query_generator: Optional query generator instance.
        detailed_prompts: Whether to use detailed prompts in nodes.

    Returns:
        Compiled StateGraph for interviews.

    Example:
        >>> graph = build_interview_graph()
        >>> result = graph.invoke({"analyst": analyst, "messages": [...]})
    """
    logger.info("Building interview subgraph")

    # Initialize default tools if not provided
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        logger.debug("Using default LLM: gpt-4o")

    if web_search_tool is None:
        web_search_tool = WebSearchTool(max_results=3)

    if wiki_search_tool is None:
        wiki_search_tool = WikipediaSearchTool(load_max_docs=2)

    if query_generator is None:
        query_generator = SearchQueryGenerator(llm=llm)

    # Create graph builder
    builder = StateGraph(InterviewState)

    # Define node functions with partial application for injected dependencies
    def ask_question_node(state: InterviewState) -> dict[str, Any]:
        return generate_question(state, llm=llm, detailed_prompts=detailed_prompts)

    def search_web_wrapper(state: InterviewState) -> dict[str, Any]:
        return search_web_node(state, search_tool=web_search_tool, query_generator=query_generator)

    def search_wikipedia_wrapper(state: InterviewState) -> dict[str, Any]:
        return search_wikipedia_node(
            state, search_tool=wiki_search_tool, query_generator=query_generator
        )

    def answer_question_node(state: InterviewState) -> dict[str, Any]:
        return generate_answer(state, llm=llm, detailed_prompts=detailed_prompts)

    def save_interview_node(state: InterviewState) -> dict[str, Any]:
        return save_interview(state)

    def write_section_node(state: InterviewState) -> dict[str, Any]:
        return write_section(state, llm=llm, detailed_prompts=detailed_prompts)

    # Add nodes
    builder.add_node("ask_question", ask_question_node)
    builder.add_node("search_web", search_web_wrapper)
    builder.add_node("search_wikipedia", search_wikipedia_wrapper)
    builder.add_node("answer_question", answer_question_node)
    builder.add_node("save_interview", save_interview_node)
    builder.add_node("write_section", write_section_node)

    # Define edges
    # Start -> ask question
    builder.add_edge(START, "ask_question")

    # After asking question, do both searches in parallel
    builder.add_edge("ask_question", "search_web")
    builder.add_edge("ask_question", "search_wikipedia")

    # Both searches -> answer question
    builder.add_edge("search_web", "answer_question")
    builder.add_edge("search_wikipedia", "answer_question")

    # After answer, route to either ask another question or save interview
    builder.add_conditional_edges(
        "answer_question", route_messages, ["ask_question", "save_interview"]
    )

    # Save interview -> write section -> END
    builder.add_edge("save_interview", "write_section")
    builder.add_edge("write_section", END)

    # Compile the graph
    graph = cast(
        CompiledStateGraph[InterviewState, None, InterviewState, InterviewState], builder.compile()
    )
    logger.info("Interview subgraph built successfully")

    return graph


def create_interview_config(
    max_num_turns: int = 2,
    web_max_results: int = 3,
    wiki_max_docs: int = 2,
    detailed_prompts: bool = False,
    llm_model: str = "gpt-4o",
    llm_temperature: float = 0.0,
) -> dict[str, Any]:
    """Create configuration for interview graph.

    Args:
        max_num_turns: Maximum interview turns (question-answer pairs).
        web_max_results: Maximum web search results.
        wiki_max_docs: Maximum Wikipedia documents.
        detailed_prompts: Whether to use detailed prompts.
        llm_model: LLM model name.
        llm_temperature: LLM temperature setting.

    Returns:
        Configuration dictionary.

    Example:
        >>> config = create_interview_config(max_num_turns=3)
        >>> print(config['max_num_turns'])
    """
    return {
        "max_num_turns": max_num_turns,
        "web_max_results": web_max_results,
        "wiki_max_docs": wiki_max_docs,
        "detailed_prompts": detailed_prompts,
        "llm_model": llm_model,
        "llm_temperature": llm_temperature,
    }


def get_interview_graph_info() -> dict[str, Any]:
    """Get information about the interview graph structure.

    Returns:
        Dictionary describing the graph structure and flow.

    Example:
        >>> info = get_interview_graph_info()
        >>> print(info['description'])
    """
    return {
        "name": "Interview Subgraph",
        "description": "Manages analyst-expert interviews with search integration",
        "nodes": [
            "ask_question",
            "search_web",
            "search_wikipedia",
            "answer_question",
            "save_interview",
            "write_section",
        ],
        "entry_point": "ask_question",
        "exit_point": "write_section",
        "parallel_nodes": ["search_web", "search_wikipedia"],
        "conditional_edges": {"answer_question": ["ask_question", "save_interview"]},
        "max_iterations": "Determined by max_num_turns in state",
        "output": "Report section with citations",
    }


# Visualization helper
def visualize_interview_graph(
    graph: CompiledStateGraph[InterviewState, None, InterviewState, InterviewState] | None = None,
    output_path: str = "interview_graph.png",
) -> None:
    """Visualize the interview graph structure.

    Args:
        graph: Optional graph instance. If None, builds a new one.
        output_path: Path to save the visualization.

    Example:
        >>> visualize_interview_graph(output_path="my_graph.png")
    """
    try:
        from contextlib import suppress
        from pathlib import Path

        from IPython.display import Image, display

        if graph is None:
            graph = build_interview_graph()

        # Generate visualization
        img_data = graph.get_graph().draw_mermaid_png()

        # Save to file
        path = Path(output_path)
        with path.open("wb") as f:
            f.write(img_data)

        logger.info(f"Graph visualization saved to {output_path}")

        # Display in notebook if available
        with suppress(Exception):
            display(Image(img_data))  # type: ignore
    except ImportError:
        logger.warning("IPython not available, skipping visualization")
    except Exception as e:
        logger.error(f"Failed to visualize graph: {str(e)}")
