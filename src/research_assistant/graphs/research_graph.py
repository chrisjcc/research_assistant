"""Main research graph construction and management.

This module builds the top-level research graph that orchestrates analyst
creation, parallel interviews via Send() API, and final report synthesis.

Example:
    >>> from research_assistant.graphs.research_graph import build_research_graph
    >>> graph = build_research_graph()
    >>> result = graph.invoke({"topic": "AI Safety", "max_analysts": 3})
"""

import logging
from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from ..core.schemas import Analyst
from ..core.state import GenerateAnalystsState, ResearchGraphState
from ..nodes.analyst_nodes import create_analysts, human_feedback
from ..nodes.report_nodes import (
    finalize_report,
    write_conclusion,
    write_introduction,
    write_report,
)
from .interview_graph import build_interview_graph

# Configure logger
logger = logging.getLogger(__name__)


def initiate_all_interviews(state: ResearchGraphState) -> Union[str, List[Send]]:
    """Conditional edge to initiate interviews or return to analyst creation.

    This function implements the branching logic after human feedback:
    - If feedback is "approve", launches parallel interviews via Send() API
    - Otherwise, returns to analyst creation for regeneration

    Args:
        state: Current research graph state.

    Returns:
        Either "create_analysts" string or list of Send objects for parallel execution.

    Example:
        >>> # If approved, returns list of Send objects
        >>> result = initiate_all_interviews(state)
        >>> isinstance(result, list)
        True
    """
    logger.info("Evaluating interview initiation decision")

    # Check human feedback
    human_analyst_feedback = state.get("human_analyst_feedback", "approve")

    if human_analyst_feedback.lower().strip() != "approve":
        logger.info(
            f"Analysts not approved, returning to creation. "
            f"Feedback: {human_analyst_feedback[:100]}"
        )
        return "create_analysts"

    # Approved - launch interviews in parallel
    topic = state["topic"]
    analysts = state.get("analysts", [])

    if not analysts:
        logger.error("No analysts available for interviews")
        raise ValueError("Cannot initiate interviews without analysts")

    logger.info(f"Initiating {len(analysts)} parallel interviews")

    # Create Send objects for each analyst interview
    send_objects = []
    for analyst in analysts:
        initial_message = HumanMessage(
            content=f"So you said you were writing an article on {topic}?"
        )

        send_obj = Send("conduct_interview", {"analyst": analyst, "messages": [initial_message]})
        send_objects.append(send_obj)

        logger.debug(f"Created interview Send for analyst: {analyst.name}")

    return send_objects


def build_research_graph(
    llm: Optional[ChatOpenAI] = None,
    interview_graph: Optional[StateGraph] = None,
    enable_interrupts: bool = True,
    checkpointer: Optional[Any] = None,
    detailed_prompts: bool = False,
) -> StateGraph:
    """Build the main research graph with all components.

    Creates a compiled graph that orchestrates the entire research process:
    1. Create analyst personas
    2. Human review (optional interrupt)
    3. Parallel interviews (via Send API)
    4. Report synthesis
    5. Final report assembly

    Args:
        llm: Optional LLM instance for all nodes.
        interview_graph: Optional pre-built interview subgraph.
        enable_interrupts: Whether to enable human feedback interrupts.
        checkpointer: Optional checkpointer for state persistence.
        detailed_prompts: Whether to use detailed prompts.

    Returns:
        Compiled StateGraph for research workflow.

    Example:
        >>> graph = build_research_graph(enable_interrupts=True)
        >>> config = {"configurable": {"thread_id": "research-1"}}
        >>> result = graph.invoke(initial_state, config)
    """
    logger.info("Building main research graph")

    # Initialize default LLM if not provided
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        logger.debug("Using default LLM: gpt-4o")

    # Build interview subgraph if not provided
    if interview_graph is None:
        logger.debug("Building default interview subgraph")
        interview_graph = build_interview_graph(llm=llm, detailed_prompts=detailed_prompts)

    # Create graph builder
    builder = StateGraph(ResearchGraphState)

    # Define node functions with dependency injection
    def create_analysts_node(state: ResearchGraphState) -> Dict[str, Any]:
        # Convert to GenerateAnalystsState
        analysts_state: GenerateAnalystsState = {
            "topic": state["topic"],
            "max_analysts": state["max_analysts"],
            "human_analyst_feedback": state.get("human_analyst_feedback", ""),
            "analysts": state.get("analysts", []),
        }
        return create_analysts(analysts_state, llm=llm, detailed_prompts=detailed_prompts)

    def human_feedback_node(state: ResearchGraphState) -> Dict[str, Any]:
        return human_feedback(state)

    def write_report_node(state: ResearchGraphState) -> Dict[str, Any]:
        return write_report(state, llm=llm, detailed_prompts=detailed_prompts)

    def write_introduction_node(state: ResearchGraphState) -> Dict[str, Any]:
        return write_introduction(state, llm=llm, detailed_prompts=detailed_prompts)

    def write_conclusion_node(state: ResearchGraphState) -> Dict[str, Any]:
        return write_conclusion(state, llm=llm, detailed_prompts=detailed_prompts)

    def finalize_report_node(state: ResearchGraphState) -> Dict[str, Any]:
        return finalize_report(state)

    # Add nodes
    builder.add_node("create_analysts", create_analysts_node)
    builder.add_node("human_feedback", human_feedback_node)
    builder.add_node("conduct_interview", interview_graph)
    builder.add_node("write_report", write_report_node)
    builder.add_node("write_introduction", write_introduction_node)
    builder.add_node("write_conclusion", write_conclusion_node)
    builder.add_node("finalize_report", finalize_report_node)

    # Define edges
    # START -> create_analysts
    builder.add_edge(START, "create_analysts")

    # create_analysts -> human_feedback
    builder.add_edge("create_analysts", "human_feedback")

    # human_feedback -> conditional (either back to create_analysts or to interviews)
    builder.add_conditional_edges(
        "human_feedback", initiate_all_interviews, ["create_analysts", "conduct_interview"]
    )

    # After all interviews complete, write report components in parallel
    builder.add_edge("conduct_interview", "write_report")
    builder.add_edge("conduct_interview", "write_introduction")
    builder.add_edge("conduct_interview", "write_conclusion")

    # All three writing nodes -> finalize_report
    builder.add_edge(["write_conclusion", "write_report", "write_introduction"], "finalize_report")

    # finalize_report -> END
    builder.add_edge("finalize_report", END)

    # Compile with optional interrupt and checkpointer
    compile_kwargs = {}

    if enable_interrupts:
        compile_kwargs["interrupt_before"] = ["human_feedback"]
        logger.debug("Enabled interrupt before human_feedback node")

    if checkpointer is None and enable_interrupts:
        # Use in-memory checkpointer for interrupts
        checkpointer = MemorySaver()
        logger.debug("Using MemorySaver checkpointer")

    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer

    graph = builder.compile(**compile_kwargs)

    logger.info("Main research graph built successfully")

    return graph


def create_research_config(
    topic: str,
    max_analysts: int = 3,
    max_interview_turns: int = 2,
    human_analyst_feedback: str = "",
    detailed_prompts: bool = False,
    enable_interrupts: bool = True,
    llm_model: str = "gpt-4o",
    llm_temperature: float = 0.0,
    web_max_results: int = 3,
    wiki_max_docs: int = 2,
) -> Dict[str, Any]:
    """Create a complete configuration for research execution.

    Args:
        topic: Research topic to investigate.
        max_analysts: Maximum number of analysts to create.
        max_interview_turns: Maximum Q&A turns per interview.
        human_analyst_feedback: Initial feedback or "approve" to skip review.
        detailed_prompts: Whether to use detailed prompt instructions.
        enable_interrupts: Whether to enable human feedback interrupts.
        llm_model: LLM model name.
        llm_temperature: LLM temperature setting.
        web_max_results: Maximum web search results per query.
        wiki_max_docs: Maximum Wikipedia documents per query.

    Returns:
        Configuration dictionary with all settings.

    Example:
        >>> config = create_research_config(
        ...     topic="Quantum Computing",
        ...     max_analysts=4
        ... )
    """
    return {
        "topic": topic,
        "max_analysts": max_analysts,
        "max_interview_turns": max_interview_turns,
        "human_analyst_feedback": human_analyst_feedback,
        "detailed_prompts": detailed_prompts,
        "enable_interrupts": enable_interrupts,
        "llm": {"model": llm_model, "temperature": llm_temperature},
        "search": {"web_max_results": web_max_results, "wiki_max_docs": wiki_max_docs},
    }


def get_research_graph_info() -> Dict[str, Any]:
    """Get information about the research graph structure.

    Returns:
        Dictionary describing the graph structure and flow.

    Example:
        >>> info = get_research_graph_info()
        >>> print(info['description'])
    """
    return {
        "name": "Research Graph",
        "description": "Orchestrates multi-analyst research with parallel interviews",
        "nodes": [
            "create_analysts",
            "human_feedback",
            "conduct_interview (subgraph)",
            "write_report",
            "write_introduction",
            "write_conclusion",
            "finalize_report",
        ],
        "entry_point": "create_analysts",
        "exit_point": "finalize_report",
        "interrupt_points": ["human_feedback"],
        "parallel_execution": {
            "interviews": "Via Send() API - one per analyst",
            "report_writing": ["write_report", "write_introduction", "write_conclusion"],
        },
        "conditional_edges": {"human_feedback": ["create_analysts", "conduct_interview"]},
        "output": "Complete research report with introduction, insights, conclusion, and sources",
    }


def run_research(
    topic: str,
    max_analysts: int = 3,
    max_interview_turns: int = 2,
    human_analyst_feedback: str = "approve",
    enable_interrupts: bool = False,
    detailed_prompts: bool = False,
    thread_id: str = "default",
) -> Dict[str, Any]:
    """Convenience function to run complete research workflow.

    Args:
        topic: Research topic to investigate.
        max_analysts: Maximum number of analysts to create.
        max_interview_turns: Maximum Q&A turns per interview.
        human_analyst_feedback: Feedback or "approve" to proceed.
        enable_interrupts: Whether to enable interrupts (requires manual continuation).
        detailed_prompts: Whether to use detailed prompts.
        thread_id: Thread ID for checkpointing.

    Returns:
        Final state dictionary with complete report.

    Example:
        >>> result = run_research(
        ...     topic="Large Language Models",
        ...     max_analysts=3,
        ...     human_analyst_feedback="approve"
        ... )
        >>> print(result['final_report'][:100])
    """
    logger.info(f"Starting research on topic: {topic}")

    # Build graph
    graph = build_research_graph(
        enable_interrupts=enable_interrupts, detailed_prompts=detailed_prompts
    )

    # Create initial state
    initial_state: ResearchGraphState = {
        "topic": topic,
        "max_analysts": max_analysts,
        "human_analyst_feedback": human_analyst_feedback,
        "analysts": [],
        "sections": [],
        "introduction": "",
        "content": "",
        "conclusion": "",
        "final_report": "",
    }

    # Add max_num_turns to state for interview nodes
    # This is a bit of a hack - in production you'd pass this via config
    for key in list(initial_state.keys()):
        if key.startswith("_"):
            continue

    # Configure execution
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Invoke graph
        if enable_interrupts:
            logger.warning(
                "Interrupts enabled - graph will pause for human feedback. "
                "Use .stream() or manual .invoke() continuation instead."
            )

        final_state = graph.invoke(initial_state, config)

        logger.info("Research completed successfully")
        return final_state

    except Exception as e:
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        raise


def stream_research(
    topic: str,
    max_analysts: int = 3,
    human_analyst_feedback: str = "approve",
    detailed_prompts: bool = False,
    thread_id: str = "default",
):
    """Stream research execution for real-time updates.

    Args:
        topic: Research topic to investigate.
        max_analysts: Maximum number of analysts to create.
        human_analyst_feedback: Feedback or "approve" to proceed.
        detailed_prompts: Whether to use detailed prompts.
        thread_id: Thread ID for checkpointing.

    Yields:
        State updates as the graph executes.

    Example:
        >>> for update in stream_research(topic="AI Ethics"):
        ...     print(f"Node: {update[0]}, State keys: {list(update[1].keys())}")
    """
    logger.info(f"Starting streaming research on topic: {topic}")

    # Build graph with checkpointer for streaming
    graph = build_research_graph(
        enable_interrupts=False,  # No interrupts for streaming
        detailed_prompts=detailed_prompts,
        checkpointer=MemorySaver(),
    )

    # Create initial state
    initial_state: ResearchGraphState = {
        "topic": topic,
        "max_analysts": max_analysts,
        "human_analyst_feedback": human_analyst_feedback,
        "analysts": [],
        "sections": [],
        "introduction": "",
        "content": "",
        "conclusion": "",
        "final_report": "",
    }

    # Configure execution
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Stream execution
        for update in graph.stream(initial_state, config):
            yield update

        logger.info("Research streaming completed")

    except Exception as e:
        logger.error(f"Research streaming failed: {str(e)}", exc_info=True)
        raise


# Visualization helper
def visualize_research_graph(
    graph: Optional[StateGraph] = None, output_path: str = "research_graph.png"
) -> None:
    """Visualize the research graph structure.

    Args:
        graph: Optional graph instance. If None, builds a new one.
        output_path: Path to save the visualization.

    Example:
        >>> visualize_research_graph(output_path="my_graph.png")
    """
    try:
        from IPython.display import Image, display

        if graph is None:
            graph = build_research_graph()

        # Generate visualization
        img_data = graph.get_graph().draw_mermaid_png()

        # Save to file
        with open(output_path, "wb") as f:
            f.write(img_data)

        logger.info(f"Graph visualization saved to {output_path}")

        # Display in notebook if available
        try:
            display(Image(img_data))
        except:
            pass

    except ImportError:
        logger.warning("IPython not available, skipping visualization")
    except Exception as e:
        logger.error(f"Failed to visualize graph: {str(e)}")


# Utility for handling interrupted execution
def continue_research(
    graph: StateGraph, thread_id: str, human_feedback: Optional[str] = None
) -> Dict[str, Any]:
    """Continue research execution after interrupt.

    Used when graph is interrupted at human_feedback node. Allows updating
    the feedback and continuing execution.

    Args:
        graph: The research graph instance.
        thread_id: Thread ID of the interrupted execution.
        human_feedback: Updated human feedback. None to continue with existing state.

    Returns:
        Final state after continuation.

    Example:
        >>> # After interrupt, provide feedback and continue
        >>> graph = build_research_graph(enable_interrupts=True)
        >>> # ... initial invoke that gets interrupted ...
        >>> final_state = continue_research(
        ...     graph,
        ...     thread_id="research-1",
        ...     human_feedback="approve"
        ... )
    """
    logger.info(f"Continuing research for thread_id: {thread_id}")

    config = {"configurable": {"thread_id": thread_id}}

    # Get current state
    try:
        current_state = graph.get_state(config)
        logger.debug(f"Retrieved state for thread {thread_id}")
    except Exception as e:
        logger.error(f"Failed to retrieve state: {str(e)}")
        raise ValueError(f"No state found for thread_id: {thread_id}") from e

    # Update feedback if provided
    if human_feedback is not None:
        logger.info(f"Updating human feedback: {human_feedback[:100]}")
        # Update the state with new feedback
        updated_values = {"human_analyst_feedback": human_feedback}
        graph.update_state(config, updated_values)

    # Continue execution
    try:
        final_state = graph.invoke(None, config)
        logger.info("Research continuation completed")
        return final_state
    except Exception as e:
        logger.error(f"Failed to continue research: {str(e)}", exc_info=True)
        raise


def get_research_state(graph: StateGraph, thread_id: str) -> Dict[str, Any]:
    """Get the current state of a research execution.

    Useful for inspecting state during or after execution, especially
    when using interrupts.

    Args:
        graph: The research graph instance.
        thread_id: Thread ID of the execution.

    Returns:
        Current state dictionary.

    Example:
        >>> state = get_research_state(graph, "research-1")
        >>> print(f"Analysts: {len(state['analysts'])}")
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_snapshot = graph.get_state(config)
        return state_snapshot.values
    except Exception as e:
        logger.error(f"Failed to get state: {str(e)}")
        raise ValueError(f"No state found for thread_id: {thread_id}") from e


def list_research_checkpoints(
    graph: StateGraph, thread_id: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """List checkpoints for a research execution.

    Args:
        graph: The research graph instance.
        thread_id: Thread ID of the execution.
        limit: Maximum number of checkpoints to return.

    Returns:
        List of checkpoint information dictionaries.

    Example:
        >>> checkpoints = list_research_checkpoints(graph, "research-1")
        >>> for cp in checkpoints:
        ...     print(f"Step: {cp['step']}, Node: {cp['node']}")
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        history = []
        for state in graph.get_state_history(config):
            history.append(
                {
                    "step": state.config.get("configurable", {}).get("checkpoint_id"),
                    "values": state.values,
                    "next": state.next,
                    "metadata": state.metadata,
                }
            )

            if len(history) >= limit:
                break

        return history
    except Exception as e:
        logger.error(f"Failed to list checkpoints: {str(e)}")
        return []


# Factory function for creating complete research system
def create_research_system(
    llm_model: str = "gpt-4o",
    llm_temperature: float = 0.0,
    enable_interrupts: bool = True,
    detailed_prompts: bool = False,
    web_max_results: int = 3,
    wiki_max_docs: int = 2,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Factory function to create a complete configured research system.

    Args:
        llm_model: LLM model name.
        llm_temperature: LLM temperature setting.
        enable_interrupts: Whether to enable human feedback interrupts.
        detailed_prompts: Whether to use detailed prompts.
        web_max_results: Maximum web search results.
        wiki_max_docs: Maximum Wikipedia documents.
        use_cache: Whether to enable search caching.

    Returns:
        Dictionary with 'graph', 'llm', and 'config' keys.

    Example:
        >>> system = create_research_system(llm_model="gpt-4")
        >>> graph = system['graph']
        >>> result = graph.invoke(initial_state)
    """
    logger.info("Creating research system")

    # Initialize LLM
    llm = ChatOpenAI(model=llm_model, temperature=llm_temperature)

    # Import tools
    from ..tools.search import WebSearchTool, WikipediaSearchTool

    # Initialize search tools
    web_tool = WebSearchTool(max_results=web_max_results, use_cache=use_cache)
    wiki_tool = WikipediaSearchTool(load_max_docs=wiki_max_docs, use_cache=use_cache)

    # Build interview graph with tools
    interview_graph = build_interview_graph(
        llm=llm,
        web_search_tool=web_tool,
        wiki_search_tool=wiki_tool,
        detailed_prompts=detailed_prompts,
    )

    # Build main research graph
    research_graph = build_research_graph(
        llm=llm,
        interview_graph=interview_graph,
        enable_interrupts=enable_interrupts,
        detailed_prompts=detailed_prompts,
    )

    config = {
        "llm_model": llm_model,
        "llm_temperature": llm_temperature,
        "enable_interrupts": enable_interrupts,
        "detailed_prompts": detailed_prompts,
        "web_max_results": web_max_results,
        "wiki_max_docs": wiki_max_docs,
        "use_cache": use_cache,
    }

    logger.info("Research system created successfully")

    return {
        "graph": research_graph,
        "interview_graph": interview_graph,
        "llm": llm,
        "web_tool": web_tool,
        "wiki_tool": wiki_tool,
        "config": config,
    }


# Example usage patterns
def get_usage_examples() -> str:
    """Get example usage patterns for the research system.

    Returns:
        String containing example code snippets.
    """
    return """
RESEARCH SYSTEM USAGE EXAMPLES
================================

1. BASIC RESEARCH (NO INTERRUPTS)
----------------------------------
from research_assistant.graphs.research_graph import run_research

result = run_research(
    topic="Quantum Computing Applications",
    max_analysts=3,
    human_analyst_feedback="approve"
)

print(result['final_report'])

2. WITH HUMAN REVIEW (INTERRUPTS)
----------------------------------
from research_assistant.graphs.research_graph import (
    build_research_graph,
    continue_research
)

# Build graph with interrupts
graph = build_research_graph(enable_interrupts=True)

# Initial state
initial_state = {
    "topic": "AI Ethics",
    "max_analysts": 3,
    "human_analyst_feedback": "",
    "analysts": [],
    "sections": [],
    "introduction": "",
    "content": "",
    "conclusion": "",
    "final_report": ""
}

# Start execution (will pause at human_feedback)
config = {"configurable": {"thread_id": "research-1"}}
graph.invoke(initial_state, config)

# Review analysts and provide feedback
state = get_research_state(graph, "research-1")
print(f"Analysts created: {len(state['analysts'])}")

# Continue with feedback
final_state = continue_research(
    graph,
    thread_id="research-1",
    human_feedback="approve"
)

print(final_state['final_report'])

3. STREAMING EXECUTION
-----------------------
from research_assistant.graphs.research_graph import stream_research

for update in stream_research(
    topic="Machine Learning in Healthcare",
    max_analysts=4
):
    node_name = list(update.keys())[0]
    print(f"Completed node: {node_name}")

4. CUSTOM CONFIGURATION
-----------------------
from research_assistant.graphs.research_graph import create_research_system

system = create_research_system(
    llm_model="gpt-4",
    enable_interrupts=True,
    detailed_prompts=True,
    web_max_results=5
)

graph = system['graph']
result = graph.invoke(initial_state, config)

5. REGENERATING ANALYSTS
-------------------------
# After initial generation, provide feedback
graph.invoke(initial_state, config)

# Get current state and review
state = get_research_state(graph, "research-1")

# Provide specific feedback for regeneration
final_state = continue_research(
    graph,
    thread_id="research-1",
    human_feedback="Need more focus on policy perspectives and less on technical details"
)

# Review new analysts
print(f"Regenerated {len(final_state['analysts'])} analysts")
"""
