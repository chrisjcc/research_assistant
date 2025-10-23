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
