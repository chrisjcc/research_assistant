"""Gradio web interface for the Research Assistant.

This module provides an interactive web UI for running research with real-time
progress tracking, analyst review, and result download.

Usage:
    python app/gradio_app.py
    
    Or with custom settings:
    python app/gradio_app.py --port 7860 --share
"""

import gradio as gr
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import time

from research_assistant.config import load_config,
from research_assistant.core.state import create_initial_research_state
from research_assistant.utils import setup_logging, get_logger, get_metrics, format_duration
from research_assistant.core.schemas import Analyst

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Global state for the app
APP_STATE = {
    "graph": None,
    "current_research": None,
    "thread_id": None,
}


# ============================================================================
# Helper Functions
# ============================================================================

def initialize_graph() -> None:
    """Initialize the research graph on startup."""
    try:
        logger.info("Initializing research graph...")
        config = load_config()
        
        from research_assistant.graphs.research_graph import create_research_system
        system = create_research_system(
            llm_model=config.llm.model,
            enable_interrupts=True,
            detailed_prompts=False
        )
        
        APP_STATE["graph"] = system["graph"]
        logger.info("Research graph initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize graph: {e}", exc_info=True)
        raise


def format_analyst_for_display(analyst: Analyst) -> str:
    """Format analyst for display in UI.
    
    Args:
        analyst: Analyst instance.
        
    Returns:
        Formatted markdown string.
    """
    return f"""### {analyst.name}
**Role:** {analyst.role}  
**Affiliation:** {analyst.affiliation}  
**Focus:** {analyst.description}
"""


def create_progress_message(
    stage: str,
    details: str = "",
    progress: float = 0.0
) -> Tuple[str, float]:
    """Create progress message and value.
    
    Args:
        stage: Current stage name.
        details: Additional details.
        progress: Progress value (0-1).
        
    Returns:
        Tuple of (message, progress).
    """
    stages = {
        "init": "🔧 Initializing research...",
        "creating_analysts": "👥 Creating analyst personas...",
        "review": "👀 Review analysts (waiting for approval)...",
        "interviewing": "💬 Conducting interviews...",
        "writing": "✍️ Writing report sections...",
        "synthesizing": "🔄 Synthesizing final report...",
        "complete": "✅ Research complete!",
        "error": "❌ Error occurred"
    }
    
    base_message = stages.get(stage, stage)
    if details:
        message = f"{base_message}\n{details}"
    else:
        message = base_message
    
    return message, progress


# ============================================================================
# Core Research Functions
# ============================================================================

def start_research(
    topic: str,
    max_analysts: int,
    max_turns: int,
    detailed_prompts: bool,
    progress=gr.Progress()
) -> Tuple[str, str, str, str]:
    """Start research process.
    
    Args:
        topic: Research topic.
        max_analysts: Number of analysts to create.
        max_turns: Maximum interview turns.
        detailed_prompts: Use detailed prompts.
        progress: Gradio progress tracker.
        
    Returns:
        Tuple of (status, analysts_display, intermediate_results, error_message).
    """
    try:
        # Validate inputs
        if not topic or len(topic.strip()) < 3:
            return (
                "❌ Error: Topic must be at least 3 characters",
                "",
                "",
                "Topic too short"
            )
        
        if max_analysts < 1 or max_analysts > 10:
            return (
                "❌ Error: Number of analysts must be between 1 and 10",
                "",
                "",
                "Invalid analyst count"
            )
        
        # Sanitize user input before logging
        sanitized_topic = topic.replace('\r\n', '').replace('\n', '').replace('\r', '')
        
        # Update progress
        progress(0.1, desc="Initializing research...")
        
        # Initialize graph if needed
        if APP_STATE["graph"] is None:
            initialize_graph()
        
        graph = APP_STATE["graph"]
        
        # Create thread ID
        thread_id = f"research-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        APP_STATE["thread_id"] = thread_id
        
        # Create initial state
        progress(0.2, desc="Creating analyst personas...")
        
        initial_state = create_initial_research_state(
            topic=topic.strip(),
            max_analysts=max_analysts
        )
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Start execution (will pause at human_feedback)
        logger.info(f"Starting research on: {sanitized_topic}")
        
        try:
            graph.invoke(initial_state, config)
        except Exception as e:
            # Expected to interrupt at human_feedback
            logger.debug(f"Graph interrupted (expected): {e}")
        
        progress(0.4, desc="Analysts created, awaiting review...")
        
        # Get current state to retrieve analysts
        state = graph.get_state(config)
        analysts = state.values.get("analysts", [])
        
        if not analysts:
            return (
                "❌ Error: No analysts were created",
                "",
                "",
                "Failed to create analysts"
            )
        
        # Store in app state
        APP_STATE["current_research"] = {
            "topic": topic,
            "analysts": analysts,
            "state": state
        }
        
        # Format analysts for display
        analysts_md = "# Generated Analysts\n\n"
        analysts_md += "Please review the analysts below and approve or provide feedback.\n\n"
        
        for i, analyst in enumerate(analysts, 1):
            analysts_md += f"{i}. " + format_analyst_for_display(analyst) + "\n"
        
        status = f"✅ Created {len(analysts)} analysts. Please review and approve."
        
        progress(0.5, desc="Awaiting analyst approval...")
        
        return status, analysts_md, "", ""
        
    except Exception as e:
        logger.error(f"Error starting research: {e}", exc_info=True)
        return (
            f"❌ Error: {str(e)}",
            "",
            "",
            str(e)
        )


def approve_analysts(
    feedback: str,
    progress=gr.Progress()
) -> Tuple[str, str, str]:
    """Approve analysts and continue research.
    
    Args:
        feedback: Human feedback ("approve" or custom feedback).
        progress: Gradio progress tracker.
        
    Returns:
        Tuple of (status, intermediate_results, final_report).
    """
    try:
        if APP_STATE["thread_id"] is None:
            return (
                "❌ Error: No active research. Please start research first.",
                "",
                ""
            )
        
        graph = APP_STATE["graph"]
        thread_id = APP_STATE["thread_id"]
        config = {"configurable": {"thread_id": thread_id}}
        
        # Update state with feedback
        feedback_text = feedback.strip() if feedback else "approve"
        
        sanitized_feedback = feedback_text.replace('\r','').replace('\n','')
        logger.info(f"Processing feedback: {sanitized_feedback[:50]}")
        
        if feedback_text.lower() != "approve":
            # Regenerate analysts with feedback
            progress(0.3, desc="Regenerating analysts with feedback...")
            
            graph.update_state(
                config,
                {"human_analyst_feedback": feedback_text}
            )
            
            # Continue execution
            graph.invoke(None, config)
            
            # Get updated analysts
            state = graph.get_state(config)
            analysts = state.values.get("analysts", [])
            
            return (
                f"✅ Regenerated {len(analysts)} analysts. Please review again.",
                "",
                ""
            )
        
        # Approve and continue
        progress(0.5, desc="Starting interviews...")
        
        graph.update_state(config, {"human_analyst_feedback": "approve"})
        
        # Track progress through execution
        start_time = time.time()
        analysts = APP_STATE["current_research"]["analysts"]
        num_analysts = len(analysts)
        
        # Continue execution with streaming updates
        intermediate_md = "# Research Progress\n\n"
        
        for i, analyst in enumerate(analysts):
            progress_val = 0.5 + (0.3 * (i / num_analysts))
            progress(
                progress_val,
                desc=f"Interviewing analyst {i+1}/{num_analysts}: {analyst.name}"
            )
            intermediate_md += f"### Analyst {i+1}: {analyst.name}\n"
            intermediate_md += f"Status: Conducting interview...\n\n"
        
        # Continue graph execution
        progress(0.8, desc="Synthesizing final report...")
        
        final_state = graph.invoke(None, config)
        
        # Extract results
        final_report = final_state.get("final_report", "")
        
        if not final_report:
            return (
                "❌ Error: Failed to generate final report",
                intermediate_md,
                ""
            )
        
        # Get metrics
        metrics = get_metrics()
        duration = time.time() - start_time
        
        # Update intermediate results
        intermediate_md += f"\n### Research Completed\n\n"
        intermediate_md += f"- **Duration:** {format_duration(duration)}\n"
        intermediate_md += f"- **API Calls:** {metrics.get('api_calls', 0)}\n"
        intermediate_md += f"- **Tokens Used:** {metrics.get('total_tokens', 0):,}\n"
        
        progress(1.0, desc="Complete!")
        
        logger.info(f"Research completed in {format_duration(duration)}")
        
        return (
            "✅ Research complete! Download your report below.",
            intermediate_md,
            final_report
        )
        
    except Exception as e:
        logger.error(f"Error during research: {e}", exc_info=True)
        return (
            f"❌ Error: {str(e)}",
            "",
            ""
        )


def regenerate_analysts(
    feedback: str,
    progress=gr.Progress()
) -> Tuple[str, str]:
    """Regenerate analysts with feedback.
    
    Args:
        feedback: Feedback for regeneration.
        progress: Gradio progress tracker.
        
    Returns:
        Tuple of (status, analysts_display).
    """
    try:
        if not feedback or feedback.strip().lower() == "approve":
            return (
                "⚠️ Please provide specific feedback for regeneration.",
                ""
            )
        
        progress(0.3, desc="Regenerating analysts...")
        
        # Update with feedback and regenerate
        status, analysts_md, _, error = start_research(
            topic=APP_STATE["current_research"]["topic"],
            max_analysts=len(APP_STATE["current_research"]["analysts"]),
            max_turns=2,
            detailed_prompts=False,
            progress=progress
        )
        
        return status, analysts_md
        
    except Exception as e:
        logger.error(f"Error regenerating analysts: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", ""


# ============================================================================
# UI Components
# ============================================================================

def create_interface() -> gr.Blocks:
    """Create the Gradio interface.
    
    Returns:
        Gradio Blocks interface.
    """
    with gr.Blocks(
        title="Research Assistant",
        theme=gr.themes.Soft(),
        css="""
        .progress-container {padding: 20px; background: #f5f5f5; border-radius: 8px;}
        .analyst-card {padding: 15px; margin: 10px 0; background: white; border-radius: 8px; border: 1px solid #e0e0e0;}
        .status-success {color: #28a745; font-weight: bold;}
        .status-error {color: #dc3545; font-weight: bold;}
        """
    ) as interface:
        
        gr.Markdown(
            """
            # 🔬 AI Research Assistant
            
            Generate comprehensive research reports with AI-powered analyst personas.
            Each analyst brings a unique perspective to investigate your topic.
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                # Input Section
                gr.Markdown("## 📝 Research Configuration")
                
                topic_input = gr.Textbox(
                    label="Research Topic",
                    placeholder="Enter your research topic (e.g., 'AI Safety' or 'Quantum Computing Applications')",
                    lines=2
                )
                
                with gr.Row():
                    max_analysts_input = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        label="Number of Analysts",
                        info="More analysts = more comprehensive research"
                    )
                    
                    max_turns_input = gr.Slider(
                        minimum=1,
                        maximum=5,
                        value=2,
                        step=1,
                        label="Interview Depth",
                        info="Number of question-answer turns per interview"
                    )
                
                detailed_prompts_input = gr.Checkbox(
                    label="Use Detailed Prompts",
                    value=False,
                    info="More detailed instructions (slower but potentially better)"
                )
                
                start_btn = gr.Button(
                    "🚀 Start Research",
                    variant="primary",
                    size="lg"
                )
                
                status_output = gr.Markdown(
                    label="Status",
                    value="Ready to start research..."
                )
            
            with gr.Column(scale=1):
                # Info panel
                gr.Markdown(
                    """
                    ### ℹ️ How it works
                    
                    1. **Configure** your research topic and parameters
                    2. **Generate** AI analyst personas
                    3. **Review** and approve analysts
                    4. **Wait** while analysts conduct research
                    5. **Download** your comprehensive report
                    
                    ### ⏱️ Estimated Time
                    - 2 analysts: ~2-3 minutes
                    - 3 analysts: ~3-5 minutes
                    - 5 analysts: ~5-8 minutes
                    
                    ### 💡 Tips
                    - Be specific with your topic
                    - Use 3-5 analysts for best results
                    - Provide feedback if analysts need adjustment
                    """
                )
        
        gr.Markdown("---")
        
        # Analyst Review Section
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 👥 Generated Analysts")
                
                analysts_display = gr.Markdown(
                    value="Analysts will appear here after generation..."
                )
                
                with gr.Row():
                    feedback_input = gr.Textbox(
                        label="Feedback (optional)",
                        placeholder="Type 'approve' to continue, or provide specific feedback for regeneration",
                        lines=2
                    )
                
                with gr.Row():
                    approve_btn = gr.Button(
                        "✅ Approve & Continue",
                        variant="primary"
                    )
                    
                    regenerate_btn = gr.Button(
                        "🔄 Regenerate with Feedback",
                        variant="secondary"
                    )
        
        gr.Markdown("---")
        
        # Results Section
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📊 Research Progress")
                
                intermediate_results = gr.Markdown(
                    value="Progress updates will appear here..."
                )
        
        gr.Markdown("---")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📄 Final Report")
                
                report_output = gr.Markdown(
                    value="Your final report will appear here..."
                )
                
                download_btn = gr.Button(
                    "💾 Download Report",
                    variant="secondary"
                )
                
                download_file = gr.File(
                    label="Download",
                    visible=False
                )
        
        # Event handlers
        start_btn.click(
            fn=start_research,
            inputs=[
                topic_input,
                max_analysts_input,
                max_turns_input,
                detailed_prompts_input
            ],
            outputs=[
                status_output,
                analysts_display,
                intermediate_results,
                gr.Textbox(visible=False)  # error output
            ]
        )
        
        approve_btn.click(
            fn=approve_analysts,
            inputs=[feedback_input],
            outputs=[
                status_output,
                intermediate_results,
                report_output
            ]
        )
        
        regenerate_btn.click(
            fn=regenerate_analysts,
            inputs=[feedback_input],
            outputs=[
                status_output,
                analysts_display
            ]
        )
        
        def save_report_to_file(report_text: str) -> Optional[str]:
            """Save report to temporary file for download."""
            if not report_text:
                return None
            
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"research_report_{timestamp}.md"
            
            filename.write_text(report_text, encoding="utf-8")
            
            return str(filename)
        
        download_btn.click(
            fn=save_report_to_file,
            inputs=[report_output],
            outputs=[download_file]
        )
        
        # Examples
        gr.Examples(
            examples=[
                ["AI Safety and Alignment", 3, 2, False],
                ["Quantum Computing Applications in Drug Discovery", 4, 2, False],
                ["Climate Change Mitigation Technologies", 3, 3, False],
                ["Large Language Models: Capabilities and Limitations", 5, 2, True],
            ],
            inputs=[
                topic_input,
                max_analysts_input,
                max_turns_input,
                detailed_prompts_input
            ]
        )
    
    return interface


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Run the Gradio application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Assistant Web UI")
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public share link"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Initialize graph on startup
    try:
        initialize_graph()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        print(f"Error: Failed to initialize research graph: {e}")
        print("Please check your configuration and API keys.")
        return
    
    # Create and launch interface
    interface = create_interface()
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        debug=args.debug,
        show_error=True
    )


if __name__ == "__main__":
    main()
