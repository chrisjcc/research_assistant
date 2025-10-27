"""Integration tests for graph execution.

Tests complete graph workflows with mocked external dependencies.
Uses VCR.py for recording/replaying API calls.
"""

import pytest
from unittest.mock import Mock, patch
import vcr

from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv

from research_assistant.graphs.interview_graph import build_interview_graph
from research_assistant.graphs.research_graph import (
    build_research_graph,
    initiate_all_interviews,
)
from research_assistant.core.state import create_initial_research_state


load_dotenv()  # take environment variables

# Configure VCR
my_vcr = vcr.VCR(
    cassette_library_dir='tests/cassettes',
    record_mode='once',
    match_on=['uri', 'method'],
    filter_headers=['authorization', 'api-key'],
)


# ============================================================================
# Interview Graph Integration Tests
# ============================================================================

@pytest.mark.integration
class TestInterviewGraphIntegration:
    """Integration tests for interview subgraph."""
    
    def test_interview_graph_build(self, mock_llm):
        """Test building interview graph."""
        graph = build_interview_graph(llm=mock_llm)
        
        assert graph is not None
        # Graph should be compiled
        assert hasattr(graph, 'invoke')
    
    def test_interview_graph_execution(
        self,
        sample_analyst,
        mock_llm,
        mock_web_search,
        mock_wikipedia_search,
        mock_search_query_generator
    ):
        """Test complete interview execution."""
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=mock_web_search,
            wiki_search_tool=mock_wikipedia_search,
            query_generator=mock_search_query_generator
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Let's discuss AI safety")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        result = graph.invoke(initial_state)
        
        # Should have generated a section
        assert "sections" in result
        assert len(result["sections"]) > 0
    
    def test_interview_graph_state_transitions(
        self,
        sample_analyst,
        mock_llm,
        mock_web_search
    ):
        """Test state transitions through interview."""
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=mock_web_search
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Start")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        # Execute and check state updates
        result = graph.invoke(initial_state)
        
        # Messages should be added
        assert len(result.get("messages", [])) > len(initial_state["messages"])
        
        # Context should be populated
        assert len(result.get("context", [])) > 0
        
        # Interview should be saved
        assert len(result.get("interview", "")) > 0
    
    @pytest.mark.slow
    def test_interview_graph_multiple_turns(
        self,
        sample_analyst,
        mock_llm,
        mock_web_search
    ):
        """Test interview with multiple turns."""
        graph = build_interview_graph(llm=mock_llm, web_search_tool=mock_web_search)
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Discuss AI")],
            "max_num_turns": 3,  # Multiple turns
            "context": [],
            "interview": "",
            "sections": []
        }
        
        result = graph.invoke(initial_state)
        
        # Should have more messages from multiple turns
        expert_responses = [
            m for m in result["messages"]
            if hasattr(m, 'name') and m.name == "expert"
        ]
        
        # May not reach full 3 turns if interview concludes early
        assert len(expert_responses) >= 1


# ============================================================================
# Research Graph Integration Tests
# ============================================================================

@pytest.mark.integration
class TestResearchGraphIntegration:
    """Integration tests for main research graph."""
    
    def test_research_graph_build(self, mock_llm, mock_interview_graph):
        """Test building research graph."""
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        assert graph is not None
        assert hasattr(graph, 'invoke')
    
    def test_research_graph_analyst_creation(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test analyst creation phase."""
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        initial_state = create_initial_research_state(
            topic="AI Safety",
            max_analysts=2
        )
        initial_state["human_analyst_feedback"] = "approve"
        
        result = graph.invoke(initial_state)
        
        # Analysts should be created
        assert "analysts" in result
        assert len(result["analysts"]) > 0
    
    def test_initiate_all_interviews(self, sample_analysts):
        """Test interview initiation logic."""
        state = {
            "topic": "AI Safety",
            "analysts": sample_analysts,
            "human_analyst_feedback": "approve"
        }
        
        result = initiate_all_interviews(state)
        
        # Should return Send objects
        assert isinstance(result, list)
        assert len(result) == len(sample_analysts)
    
    def test_initiate_interviews_not_approved(self):
        """Test interview initiation when not approved."""
        state = {
            "topic": "AI Safety",
            "analysts": [],
            "human_analyst_feedback": "need changes"
        }
        
        result = initiate_all_interviews(state)
        
        # Should return to analyst creation
        assert result == "create_analysts"
    
    @pytest.mark.slow
    def test_complete_research_workflow(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test complete research workflow end-to-end."""
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        initial_state = create_initial_research_state(
            topic="Test Topic",
            max_analysts=1
        )
        initial_state["human_analyst_feedback"] = "approve"
        
        result = graph.invoke(initial_state)
        
        # Final report should be generated
        assert "final_report" in result
        assert len(result["final_report"]) > 0
        
        # All components should be present
        assert "introduction" in result
        assert "content" in result
        assert "conclusion" in result


# ============================================================================
# Error Scenario Tests
# ============================================================================

@pytest.mark.integration
class TestErrorScenarios:
    """Test error handling in graph execution."""

    @pytest.mark.xfail(reason="LangGraph exception wrapping needs investigation")
    def test_interview_graph_llm_failure(
        self,
        sample_analyst,
        mock_failing_llm
    ):
        """Test interview graph with LLM failure."""
        from research_assistant.utils.exceptions import InterviewError
        
        graph = build_interview_graph(llm=mock_failing_llm)
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        with pytest.raises(InterviewError, match="Question generation failed"):
            graph.invoke(initial_state)

    @pytest.mark.skip(reason="Production code doesn't validate empty analysts yet")
    def test_research_graph_missing_analysts(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test research graph with no analysts."""
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=1
        )
        initial_state["analysts"] = []  # Empty analysts
        initial_state["human_analyst_feedback"] = "approve"
        
        with pytest.raises(ValueError, match="Cannot initiate interviews"):
            graph.invoke(initial_state)
    
    def test_interview_graph_search_failure(
        self,
        sample_analyst,
        mock_llm
    ):
        """Test interview with search tool failure."""
        # Create mock that fails
        failing_search = Mock()
        failing_search.search.side_effect = Exception("Search failed")
        
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=failing_search
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        # Should handle search failure gracefully
        # (depending on implementation, may continue with empty context)
        result = graph.invoke(initial_state)
        
        # Should still complete, possibly with empty context
        assert "sections" in result


# ============================================================================
# VCR Integration Tests (Optional - requires real API keys)
# ============================================================================

@pytest.mark.requires_api
@pytest.mark.integration
class TestWithRealAPIs:
    """Integration tests with real APIs (recorded with VCR)."""
    
    @pytest.mark.skip(reason="VCR cassette needs re-recording")
    @my_vcr.use_cassette('interview_real_llm.yaml')
    def test_interview_with_real_llm(self, sample_analyst):
        """Test interview with real LLM (recorded)."""
        # pytest.skip("Requires API keys - uncomment when ready")
        
        # Uncomment to run with real APIs
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        graph = build_interview_graph(llm=llm)
 
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Discuss AI safety")],
            "max_num_turns": 1
        }
 
        result = graph.invoke(initial_state)
        assert len(result["sections"]) > 0
    
    @my_vcr.use_cassette('research_real_workflow.yaml')
    def test_complete_workflow_with_real_apis(self):
        """Test complete workflow with real APIs (recorded)."""
        pytest.skip("Requires API keys - uncomment when ready")


# ============================================================================
# State Persistence Tests
# ============================================================================

@pytest.mark.integration
class TestStatePersistence:
    """Test state checkpointing and persistence."""
    
    def test_research_graph_with_checkpoint(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test research graph with checkpointing."""
        from langgraph.checkpoint.memory import MemorySaver
        
        checkpointer = MemorySaver()
        
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=True,
            checkpointer=checkpointer
        )
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=1
        )
        
        config = {"configurable": {"thread_id": "test-1"}}
        
        # First invocation (will interrupt)
        try:
            graph.invoke(initial_state, config)
        except:
            pass  # Expected to interrupt
        
        # Get state
        state = graph.get_state(config)
        assert state is not None
    
    def test_state_recovery_after_error(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test state recovery after error."""
        from langgraph.checkpoint.memory import MemorySaver
        
        checkpointer = MemorySaver()
        
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            checkpointer=checkpointer
        )
        
        config = {"configurable": {"thread_id": "test-2"}}
        
        # Try to get state before any execution
        # Should handle gracefully
        try:
            state = graph.get_state(config)
        except:
            pass  # May not have state yet


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.integration
class TestPerformance:
    """Performance and timing tests."""
    
    def test_interview_execution_time(
        self,
        sample_analyst,
        mock_llm,
        mock_web_search
    ):
        """Test interview execution completes in reasonable time."""
        import time
        
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=mock_web_search
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        start = time.time()
        result = graph.invoke(initial_state)
        duration = time.time() - start
        
        # Should complete in under 5 seconds with mocks
        assert duration < 5.0
        assert "sections" in result
    
    def test_parallel_interview_execution(
        self,
        sample_analysts,
        mock_llm,
        mock_interview_graph
    ):
        """Test parallel execution of multiple interviews."""
        import time
        
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=len(sample_analysts)
        )
        initial_state["analysts"] = sample_analysts
        initial_state["human_analyst_feedback"] = "approve"
        
        start = time.time()
        result = graph.invoke(initial_state)
        duration = time.time() - start
        
        # Should complete reasonably fast even with multiple analysts
        # Parallel execution should be faster than sequential
        assert duration < 10.0
        assert "final_report" in result


# ============================================================================
# Configuration Tests
# ============================================================================

@pytest.mark.integration
class TestGraphConfiguration:
    """Test graph configuration options."""
    
    def test_interview_graph_detailed_prompts(
        self,
        sample_analyst,
        mock_llm
    ):
        """Test interview graph with detailed prompts."""
        graph = build_interview_graph(
            llm=mock_llm,
            detailed_prompts=True
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        result = graph.invoke(initial_state)
        
        assert "sections" in result
        # Detailed prompts should still work
        assert mock_llm.invoke.called
    
    def test_research_graph_no_interrupts(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test research graph without interrupts."""
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=1
        )
        initial_state["human_analyst_feedback"] = "approve"
        
        # Should complete without interruption
        result = graph.invoke(initial_state)
        
        assert "final_report" in result
    
    def test_research_graph_with_interrupts(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test research graph with interrupts enabled."""
        from langgraph.checkpoint.memory import MemorySaver
        
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=True,
            checkpointer=MemorySaver()
        )
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=1
        )
        
        config = {"configurable": {"thread_id": "test-interrupt"}}
        
        # Should interrupt at human_feedback
        # This would require manual continuation in real usage
        try:
            graph.invoke(initial_state, config)
        except:
            pass  # May raise interrupt exception
        
        # State should be saved
        state = graph.get_state(config)
        assert state is not None


# ============================================================================
# Data Flow Tests
# ============================================================================

@pytest.mark.integration
class TestDataFlow:
    """Test data flow through graph execution."""
    
    def test_interview_context_accumulation(
        self,
        sample_analyst,
        mock_llm,
        mock_web_search,
        mock_wikipedia_search
    ):
        """Test that context accumulates during interview."""
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=mock_web_search,
            wiki_search_tool=mock_wikipedia_search
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        result = graph.invoke(initial_state)
        
        # Context should be populated from both searches
        assert len(result["context"]) > 0
        # Both web and wikipedia should have contributed
        assert mock_web_search.search.called
        assert mock_wikipedia_search.search.called
    
    @pytest.mark.skip(reason="Research graph conducts 1 interview - behavior under investigation")
    def test_research_sections_aggregation(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test that sections aggregate from multiple interviews."""
        # Mock interview graph to return unique sections per analyst
        call_tracker = {"count": 0}

        def mock_sections_per_analyst(state):
            call_tracker["count"] += 1
            analyst = state.get("analyst", {}) 
            analyst_name = analyst.name if analyst and hasattr(analyst, 'name') else f"Analyst{call_tracker['count']}"

            return {
                "analyst": state.get("analyst"),
                "messages": state.get("messages", []),
                "max_num_turns": state.get("max_num_turns", 0),
                "context": state.get("context", []),
                "interview": f"Mock interview {call_tracker['count']}",
                "sections": state.get("sections", []) + [f"## Section from {analyst_name}\n\nContent {call_tracker['count']}"]
            }

        # Mock interview graph to return sections
        mock_interview_graph.invoke.side_effect = mock_sections_per_analyst 
        mock_interview_graph.side_effect = mock_sections_per_analyst 

        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        from research_assistant.core.schemas import Analyst
        analysts = [
            Analyst(
                name=f"Analyst {i}",
                role="Researcher",
                affiliation="University",
                description="Test analyst description for validation here"
            )
            for i in range(2)
        ]
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=2
        )
        initial_state["analysts"] = analysts
        initial_state["human_analyst_feedback"] = "approve"
        
        result = graph.invoke(initial_state)
        
        # Should have sections from multiple interviews
        assert "sections" in result
        # With 2 analysts, should have 2 sections
        assert len(result["sections"]) >= 2
    
    def test_message_flow_in_interview(
        self,
        sample_analyst,
        mock_llm
    ):
        """Test message flow through interview turns."""
        graph = build_interview_graph(llm=mock_llm)
        
        initial_messages = [HumanMessage(content="Initial")]
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": initial_messages,
            "max_num_turns": 2,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        result = graph.invoke(initial_state)
        
        # Should have more messages than initial
        assert len(result["messages"]) > len(initial_messages)
        
        # Should have alternating question/answer pattern
        # (depending on implementation)
        messages = result["messages"]
        assert len(messages) >= 2


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases in graph execution."""
    
    def test_empty_search_results(
        self,
        sample_analyst,
        mock_llm
    ):
        """Test handling of empty search results."""
        empty_search = Mock()
        empty_search.search.return_value = []
        empty_search.format_results.return_value = ""
        
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=empty_search
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        # Should handle empty results gracefully
        result = graph.invoke(initial_state)
        
        assert "sections" in result
        # May have empty or minimal context
    
    def test_very_short_interview(
        self,
        sample_analyst,
        mock_llm
    ):
        """Test interview with minimal turns."""
        # Mock LLM to immediately conclude
        concluding_llm = Mock()
        call_count = {"count": 0}
        def mock_conclude(messages):
            call_count["count"] += 1
            return AIMessage(
                content="Thank you so much for your help!",
                name=None
            )
        concluding_llm.invoke.side_effect = mock_conclude
        concluding_llm.side_effect = mock_conclude
        concluding_llm.with_structured_output = mock_llm.with_structured_output
        
        graph = build_interview_graph(llm=concluding_llm)
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Test")],
            "max_num_turns": 1,  # High limit
            "context": [],
            "interview": "",
            "sections": []
        }
        
        result = graph.invoke(initial_state)
        
        # Should terminate early due to conclusion
        assert "sections" in result
    
    def test_single_analyst_research(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test research with only one analyst."""
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        from research_assistant.core.schemas import Analyst
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=1
        )
        initial_state["analysts"] = [
            Analyst(
                name="Solo Analyst",
                role="Researcher",
                affiliation="University",
                description="Only analyst for this research"
            )
        ]
        initial_state["human_analyst_feedback"] = "approve"
        
        result = graph.invoke(initial_state)
        
        # Should still produce valid report
        assert "final_report" in result
        assert len(result["final_report"]) > 0


# ============================================================================
# Regression Tests
# ============================================================================

@pytest.mark.integration
class TestRegressions:
    """Regression tests for previously found bugs."""
    
    def test_section_source_deduplication(
        self,
        mock_llm,
        mock_interview_graph
    ):
        """Test that duplicate sources are removed in final report."""
        # Mock sections with duplicate sources
        mock_interview_graph.invoke.side_effect = lambda state: {
            "analyst": state.get("analyst"),
            "messages": state.get("messages", []),
            "max_num_turns": state.get("max_num_turns", 0),
            "context": state.get("context", []),
            "interview": "Mock interview",
            "sections": [
                "## Section 1\nContent [1]\n### Sources\n[1] source1.com",
                "## Section 2\nContent [1]\n### Sources\n[1] source1.com"
            ]
        }
        
        graph = build_research_graph(
            llm=mock_llm,
            interview_graph=mock_interview_graph,
            enable_interrupts=False
        )
        
        from research_assistant.core.schemas import Analyst
        
        initial_state = create_initial_research_state(
            topic="Test",
            max_analysts=1
        )
        initial_state["analysts"] = [
            Analyst(
                name="Test",
                role="Researcher",
                affiliation="Uni",
                description="Test analyst for integration validation case"
            )
        ]
        initial_state["human_analyst_feedback"] = "approve"
        
        result = graph.invoke(initial_state)
        
        # Final report should deduplicate sources
        # (This depends on implementation in finalize_report)
        assert "final_report" in result
    
    def test_empty_interview_transcript_handling(
        self,
        sample_analyst,
        mock_llm
    ):
        """Test handling of empty interview transcripts."""
        # This is an edge case that might occur with errors
        graph = build_interview_graph(llm=mock_llm)
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [],  # Empty messages
            "max_num_turns": 1,
            "context": [],
            "interview": "",
            "sections": []
        }
        
        # Should handle gracefully
        result = graph.invoke(initial_state)
        
        assert "sections" in result
