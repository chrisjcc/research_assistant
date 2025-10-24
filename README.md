# research_assistant
LLM-based research assistant

## Directory Structure
```
research-assistant/
├── README.md
├── pyproject.toml
├── setup.cfg
├── Makefile
├── .env.example
├── .gitignore
├── environment.yaml
├── config/
│   ├── __init__.py
│   ├── default.yaml
│   ├── models/
│   │   ├── openai.yaml
│   │   └── anthropic.yaml
│   └── search/
│       ├── tavily.yaml
│       └── wikipedia.yaml
├── src/
│   └── research_assistant/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── schemas.py
│       │   └── state.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── analyst.py
│       │   ├── interviewer.py
│       │   └── writer.py
│       ├── nodes/
│       │   ├── __init__.py
│       │   ├── analyst_nodes.py
│       │   ├── interview_nodes.py
│       │   └── report_nodes.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search.py
│       │   └── retrieval.py
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── analyst_prompts.py
│       │   ├── interview_prompts.py
│       │   └── report_prompts.py
│       ├── graphs/
│       │   ├── __init__.py
│       │   ├── interview_graph.py
│       │   └── research_graph.py
│       └── utils/
│           ├── __init__.py
│           ├── logging.py
│           └── formatting.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_schemas.py
│   │   ├── test_nodes.py
│   │   └── test_tools.py
│   └── integration/
│       └── test_graph.py
├── app/
│   ├── __init__.py
│   ├── gradio_app.py
│   └── streamlit_app.py
└── docs/
    ├── architecture.md
    ├── api.md
    └── usage.md
```

## Graph Flow

```
START → ask_question → [search_web, search_wikipedia] (parallel)
                     ↓
            answer_question → route (ask_question OR save_interview)
                     ↓
            save_interview → write_section → END
```

**Features:**
- Parallel search execution (web + Wikipedia)
- Conditional routing based on interview progress
- Integrated tool instances with dependency injection
- Configurable max turns and search parameters

**Utilities:**
- `create_interview_config()` - Configuration factory
- `get_interview_graph_info()` - Graph structure info
- `visualize_interview_graph()` - PNG visualization

#### 2. **`research_graph.py`** - Main Research Orchestrator
**Main Components:**
- `initiate_all_interviews()` - Conditional edge for Send() API
- `build_research_graph()` - Complete research graph builder
- `run_research()` - Convenience function for full execution
- `stream_research()` - Generator for streaming updates
- `continue_research()` - Resume after interrupt
- `create_research_system()` - Factory for complete system

**Graph Flow:**
```
START → create_analysts → human_feedback → [conduct_interview×N] (parallel via Send)
                                          ↓
        [write_report, write_introduction, write_conclusion] (parallel)
                                          ↓
                                   finalize_report → END
```


## Configuration Manager

```
config/
├── default.yaml
├── llm/
│   ├── openai.yaml
│   ├── openai_gpt4_turbo.yaml
│   ├── anthropic.yaml
│   ├── local.yaml
│   └── cheap.yaml
├── search/
│   ├── default.yaml
│   ├── comprehensive.yaml
│   ├── minimal.yaml
│   └── no_cache.yaml
├── experiment/
│   ├── quick_test.yaml
│   ├── comprehensive.yaml
│   ├── budget_friendly.yaml
│   ├── production.yaml
│   └── local_llm.yaml
└── topic/
    ├── ai_safety.yaml
    └── climate_tech.yaml

src/research_assistant/config/
├── __init__.py
└── config.py
```


## File Structure
```
src/research_assistant/
├── py.typed                    # Type checking marker
├── utils/
│   ├── __init__.py
│   ├── logging.py             # Structured logging
│   ├── formatting.py          # Output formatting
│   ├── exceptions.py          # Custom exceptions
│   └── retry.py               # Retry & circuit breaker
├── types/
│   ├── __init__.py
│   ├── protocols.py           # Type protocols
│   └── validation.py          # Runtime validation
└── config/
    └── ...                     # (Already created)

# Configuration files
mypy.ini                        # MyPy configuration
TYPE_CHECKING_GUIDE.md         # Usage documentation
```
