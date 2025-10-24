# 🔬 AI Research Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checker: mypy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Status: Active Development](https://img.shields.io/badge/status-active%20development-orange.svg)](https://github.com)

> **An intelligent, LLM-powered research assistant built with LangGraph that conducts comprehensive research through multi-agent collaboration, structured interviews, and automated report generation.**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Web Interface](#-web-interface)
- [Testing](#-testing)
- [CI/CD](#-cicd)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)
- [Support](#-support)

---

## 🎯 Overview

The AI Research Assistant is a sophisticated research automation system that leverages large language models (LLMs) and multi-agent orchestration to conduct in-depth research on any topic. It simulates a team of expert analysts who collaboratively investigate a subject, conduct interviews, and produce comprehensive research reports.

### What It Does

1. **Generates Expert Analysts**: Creates a diverse team of AI analysts with specific expertise relevant to your research topic
2. **Conducts Structured Interviews**: Each analyst performs deep-dive interviews using web search and knowledge retrieval
3. **Synthesizes Information**: Aggregates insights from multiple perspectives into a cohesive narrative
4. **Produces Professional Reports**: Generates well-structured, citation-rich research documents

### Use Cases

- 🔍 **Academic Research**: Literature reviews, topic exploration, comparative analysis
- 💼 **Market Research**: Industry analysis, competitive intelligence, trend identification
- 📊 **Policy Analysis**: Multi-stakeholder perspectives, impact assessment
- 🚀 **Technology Assessment**: Emerging technologies, feasibility studies
- 📚 **Knowledge Synthesis**: Cross-domain insights, expert opinions compilation

---

## ✨ Key Features

### 🤖 Multi-Agent Research System
- **Dynamic Analyst Generation**: Creates specialized analysts tailored to your research question
- **Parallel Interview Execution**: Conducts multiple research streams simultaneously for efficiency
- **Human-in-the-Loop**: Review and provide feedback on generated analysts before research begins
- **Flexible Configuration**: Adjust analyst count, interview depth, and research parameters

### 🔍 Advanced Search Integration
- **Web Search**: Tavily API integration for current information
- **Wikipedia Integration**: Encyclopedic knowledge base access
- **Configurable Search Strategies**: From minimal to comprehensive search modes
- **Result Caching**: Avoid redundant API calls and reduce costs

### 📝 Intelligent Report Generation
- **Structured Output**: Introduction, methodology, findings, analysis, and conclusions
- **Citation Management**: Automatic source tracking and reference formatting
- **Markdown Export**: Professional, readable report format
- **Section-wise Generation**: Parallel generation of report sections for speed

### 🏗️ Production-Ready Architecture
- **Type Safety**: Full mypy strict mode type checking
- **Comprehensive Testing**: 90%+ test coverage with unit and integration tests
- **Structured Logging**: Detailed observability with structlog
- **Error Handling**: Robust retry mechanisms and circuit breakers
- **Configuration Management**: Hydra-based hierarchical configuration system

### 🎨 User-Friendly Interface
- **Gradio Web App**: Beautiful, interactive web interface
- **Real-time Progress**: Live updates on research progress
- **Analyst Review**: Interactive analyst approval workflow
- **Report Download**: One-click download of final reports

### 🔒 Security & Quality
- **Automated CI/CD**: GitHub Actions workflows for testing and deployment
- **Security Scanning**: 6 security tools for vulnerability detection
- **Dependency Management**: Automated updates via Dependabot
- **Code Quality**: Enforced via black, isort, flake8, and ruff

---

## 🏛️ Architecture

### System Design

The Research Assistant follows a **multi-agent graph-based architecture** built on LangGraph:

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Graph Flow                       │
└─────────────────────────────────────────────────────────────┘
                              │
                START → create_analysts
                              │
                    human_feedback (optional)
                              │
                   ┌──────────┴──────────┐
                   │                     │
          conduct_interview (Analyst 1)  conduct_interview (Analyst 2)
                   │                     │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      write_introduction  write_sections  write_conclusion
              │               │               │
              └───────────────┼───────────────┘
                              │
                      finalize_report
                              │
                            END
```

### Interview Graph (Per Analyst)

Each analyst executes a structured interview process:

```
START → ask_question
            │
      ┌─────┴─────┐
      │           │
   search_web  search_wikipedia (parallel)
      │           │
      └─────┬─────┘
            │
     answer_question
            │
      route (continue OR complete)
            │
     save_interview
            │
          END
```

### Core Components

#### 1. **State Management**
- **InterviewState**: Manages individual analyst interview sessions
- **ResearchGraphState**: Coordinates overall research workflow
- **Type-Safe**: Pydantic models with runtime validation

#### 2. **Node Functions**
- **analyst_nodes.py**: Analyst generation and management
- **interview_nodes.py**: Question asking, answering, and routing
- **report_nodes.py**: Report section generation and finalization

#### 3. **Graph Builders**
- **interview_graph.py**: Individual analyst interview orchestration
- **research_graph.py**: Multi-analyst research coordination

#### 4. **Tools & Utilities**
- **search.py**: Web and Wikipedia search integration
- **logging.py**: Structured logging with context
- **retry.py**: Retry mechanisms and circuit breakers
- **formatting.py**: Report formatting utilities

---

## 📁 Project Structure

```
research-assistant/
├── .github/                           # GitHub configuration
│   ├── workflows/                     # CI/CD workflows
│   │   ├── tests.yml                 # Testing pipeline
│   │   ├── security.yml              # Security scanning
│   │   ├── release.yml               # Release automation
│   │   └── pr.yml                    # PR validation
│   ├── dependabot.yml                # Dependency updates
│   ├── SETUP_GUIDE.md                # CI/CD setup guide
│   └── CI_CD_DOCUMENTATION.md        # Full CI/CD docs
│
├── app/                              # Web application
│   ├── gradio_app.py                 # Gradio web interface
│   ├── launch.sh                     # Unix launch script
│   └── requirements.txt              # UI dependencies
│
├── src/research_assistant/           # Main source code
│   ├── config/                       # Configuration management
│   │   ├── config.py                 # Config loader
│   │   ├── default.yaml              # Default settings
│   │   ├── llm/                      # LLM configs
│   │   ├── search/                   # Search configs
│   │   ├── experiment/               # Experiment presets
│   │   └── topic/                    # Topic-specific configs
│   │
│   ├── core/                         # Core data structures
│   │   ├── schemas.py                # Pydantic models
│   │   └── state.py                  # State definitions
│   │
│   ├── nodes/                        # Graph node functions
│   │   ├── analyst_nodes.py          # Analyst operations
│   │   ├── interview_nodes.py        # Interview logic
│   │   └── report_nodes.py           # Report generation
│   │
│   ├── graphs/                       # Graph builders
│   │   ├── interview_graph.py        # Single interview
│   │   └── research_graph.py         # Full research
│   │
│   ├── tools/                        # External integrations
│   │   └── search.py                 # Search tools
│   │
│   ├── prompts/                      # LLM prompts
│   │   ├── analyst_prompts.py        # Analyst generation
│   │   ├── interview_prompts.py      # Interview questions
│   │   └── report_prompts.py         # Report writing
│   │
│   ├── types/                        # Type definitions
│   │   ├── protocols.py              # Type protocols
│   │   └── validation.py             # Runtime validation
│   │
│   └── utils/                        # Utility functions
│       ├── logging.py                # Structured logging
│       ├── retry.py                  # Retry logic
│       ├── exceptions.py             # Custom exceptions
│       └── formatting.py             # Formatters
│
├── tests/                            # Test suite
│   ├── conftest.py                   # Shared fixtures
│   ├── unit/                         # Unit tests
│   │   ├── test_schemas.py
│   │   └── test_nodes.py
│   └── integration/                  # Integration tests
│       └── test_graph_execution.py
│
├── pyproject.toml                    # Project metadata
├── environment.yaml                  # Conda environment
├── Makefile                          # Common commands
├── pytest.ini                        # Pytest configuration
├── coverage.toml                     # Coverage settings
├── TESTING_GUIDE.md                  # Testing documentation
├── TYPE_CHECKING_GUIDE.md            # Type checking guide
└── README.md                         # This file
```

---

## 🔧 Prerequisites

### System Requirements

- **Python**: 3.10, 3.11, or 3.12
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space

### Accounts & Authentication

You'll need API keys from the following services:

#### Required
- **OpenAI API** or **Anthropic API**: For LLM access
  - Sign up: [OpenAI](https://platform.openai.com/signup) or [Anthropic](https://console.anthropic.com/)
  - Generate API key in account settings
  - Free tier available for testing

- **Tavily API**: For web search
  - Sign up: [Tavily](https://tavily.com/)
  - Get API key from dashboard
  - Free tier: 1,000 searches/month

#### Optional
- **LangSmith**: For LLM tracing and debugging
  - Sign up: [LangSmith](https://smith.langchain.com/)
  - Free tier available

### Python Dependencies

All dependencies are managed via `pyproject.toml`:
- **LangChain**: LLM orchestration framework
- **LangGraph**: Graph-based workflow engine
- **Pydantic**: Data validation and settings
- **Gradio**: Web interface framework
- **Hydra**: Configuration management
- **structlog**: Structured logging

---

## 📥 Installation

### Option 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/research-assistant.git
cd research-assistant

# Install with pip
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"
```

### Option 2: Conda Environment

```bash
# Create environment from file
conda env create -f environment.yaml

# Activate environment
conda activate research-assistant

# Install package
pip install -e ".[dev]"
```

### Option 3: Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Verify installation
python -c "from src.research_assistant import __version__; print(__version__)"

# Run tests
pytest tests/ -v

# Check type safety
mypy src/
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required variables:**

```bash
# LLM Provider (choose one)
OPENAI_API_KEY=sk-...              # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...       # Anthropic API key

# Search Provider
TAVILY_API_KEY=tvly-...            # Tavily API key

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2=true          # Enable tracing
LANGCHAIN_API_KEY=ls__...          # LangSmith API key
LANGCHAIN_PROJECT=research-assistant  # Project name
```

### Configuration System

The project uses **Hydra** for hierarchical configuration management:

#### Base Configuration (`config/default.yaml`)

```yaml
# Default research settings
max_analysts: 3
max_interview_turns: 2
report_structure:
  include_methodology: true
  include_citations: true
  
llm:
  model: gpt-4-turbo-preview
  temperature: 0.7
  max_tokens: 4000

search:
  max_results: 5
  include_domains: []
  exclude_domains: []
```

#### LLM Configurations (`config/llm/`)

- **openai.yaml**: OpenAI GPT-4 settings
- **openai_gpt4_turbo.yaml**: GPT-4 Turbo optimized
- **anthropic.yaml**: Claude 3 settings
- **local.yaml**: Local LLM configuration
- **cheap.yaml**: Budget-friendly options

#### Search Configurations (`config/search/`)

- **default.yaml**: Balanced search strategy
- **comprehensive.yaml**: Maximum depth and breadth
- **minimal.yaml**: Quick, surface-level searches
- **no_cache.yaml**: Disable caching for fresh results

#### Experiment Presets (`config/experiment/`)

- **quick_test.yaml**: Fast testing (1 analyst, 1 turn)
- **comprehensive.yaml**: Deep research (5 analysts, 3 turns)
- **budget_friendly.yaml**: Cost-optimized settings
- **production.yaml**: Production-ready defaults
- **local_llm.yaml**: Local LLM configuration

#### Usage with Overrides

```bash
# Use specific LLM
python -m research_assistant llm=anthropic

# Use comprehensive search
python -m research_assistant search=comprehensive

# Combine multiple configs
python -m research_assistant llm=cheap search=minimal experiment=quick_test

# Override specific values
python -m research_assistant max_analysts=5 max_interview_turns=3

# Topic-specific preset
python -m research_assistant topic=ai_safety
```

---

## 🚀 Quick Start

### Basic Usage

```python
from src.research_assistant.graphs.research_graph import run_research

# Define your research topic
topic = "The impact of large language models on education"

# Run research with defaults
final_report = run_research(
    topic=topic,
    max_analysts=3,
    max_interview_turns=2
)

# Access the report
print(final_report["final_report"])
```

### With Configuration

```python
from src.research_assistant.config.config import load_config
from src.research_assistant.graphs.research_graph import create_research_system

# Load configuration
cfg = load_config(overrides=["llm=anthropic", "search=comprehensive"])

# Create research system
research_system = create_research_system(cfg)

# Execute research
result = research_system.invoke({
    "topic": "Quantum computing applications in drug discovery",
    "max_analysts": 4,
    "max_interview_turns": 3
})
```

### Streaming Updates

```python
from src.research_assistant.graphs.research_graph import stream_research

# Stream research progress
for update in stream_research(
    topic="Renewable energy storage solutions",
    max_analysts=3
):
    stage = update.get("stage", "unknown")
    progress = update.get("progress", 0)
    print(f"Stage: {stage} | Progress: {progress}%")
```

### With Human Feedback

```python
from src.research_assistant.graphs.research_graph import (
    create_research_system,
    continue_research
)

# Create system with checkpointing
research_system = create_research_system(cfg, enable_interrupt=True)

# Start research (will interrupt after analyst generation)
result = research_system.invoke({"topic": "AI ethics"})

# Review analysts
analysts = result["analysts"]
for analyst in analysts:
    print(f"{analyst.name}: {analyst.role} - {analyst.affiliation}")

# Provide feedback
feedback = "Approve"  # or provide specific feedback

# Continue research
final_result = continue_research(
    research_system,
    feedback=feedback,
    checkpointer=checkpointer
)
```

---

## 💻 Usage Examples

### Example 1: Quick Research

```bash
# Using the CLI
python -m research_assistant \
  --topic "Blockchain scalability solutions" \
  --analysts 2 \
  --turns 2 \
  --output report.md
```

### Example 2: Comprehensive Analysis

```python
from src.research_assistant import ResearchAssistant

# Initialize assistant
assistant = ResearchAssistant(
    llm_config="gpt-4-turbo",
    search_config="comprehensive"
)

# Conduct in-depth research
report = assistant.research(
    topic="Climate change adaptation strategies in coastal cities",
    num_analysts=5,
    interview_depth=3,
    enable_human_review=True
)

# Export report
assistant.export_report(report, "climate_adaptation_report.pdf")
```

### Example 3: Academic Literature Review

```python
from src.research_assistant.presets import academic_research

# Use academic preset
report = academic_research(
    research_question="What are the current limitations of transformer models?",
    focus_areas=["architecture", "training", "inference"],
    include_citations=True,
    citation_style="APA"
)
```

### Example 4: Market Research

```python
from src.research_assistant.presets import market_research

# Analyze market trends
report = market_research(
    industry="Electric Vehicles",
    regions=["North America", "Europe", "Asia"],
    timeframe="2020-2024",
    include_competitors=True
)
```

---

## 🌐 Web Interface

### Launch the Gradio App

```bash
# Simple launch
python app/gradio_app.py

# Or use launch script (Linux/Mac)
./app/launch.sh

# Windows
app\launch.bat

# With options
python app/gradio_app.py --port 8080 --share
```

### Interface Features

The web interface provides:

1. **Research Configuration**
   - Topic input
   - Analyst count (1-10)
   - Interview depth (1-5)
   - Configuration presets

2. **Analyst Review**
   - View generated analysts
   - Provide feedback
   - Approve or regenerate

3. **Real-time Progress**
   - Progress bar (0-100%)
   - Stage descriptions
   - Per-analyst tracking
   - Duration estimates

4. **Results Display**
   - Formatted report preview
   - Download as Markdown
   - Share link

5. **Help & Tips**
   - Step-by-step guide
   - Best practices
   - Example topics

### Access the Interface

Open your browser and navigate to:
```
http://localhost:7860
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_schemas.py -v

# Run with markers
pytest tests/ -m "not slow"

# Run integration tests only
pytest tests/integration/ -v
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_schemas.py     # Pydantic model tests
│   └── test_nodes.py       # Node function tests
└── integration/            # Integration tests (slower)
    └── test_graph_execution.py  # End-to-end workflow tests
```

### Coverage Goals

- **Target**: 80%+ coverage
- **Current**: 90%+ coverage
- **Minimum**: 70% for new code

View coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Fixtures

Common fixtures available in `conftest.py`:
- `mock_llm`: Mocked LLM responses
- `mock_search`: Mocked search results
- `sample_analyst`: Pre-configured analyst
- `sample_state`: Pre-configured state
- `temp_config`: Temporary config file

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing documentation.

---

## 🔄 CI/CD

### Automated Workflows

GitHub Actions workflows automatically:

#### Tests (`tests.yml`)
- ✅ Run linting (flake8, black, isort, ruff)
- ✅ Execute tests on Python 3.10, 3.11, 3.12
- ✅ Generate coverage reports
- ✅ Type check with mypy

#### Security (`security.yml`)
- 🔒 Scan for vulnerabilities (Safety, pip-audit)
- 🔒 Detect secrets (TruffleHog)
- 🔒 Analyze code security (Bandit, Semgrep, CodeQL)
- 🔒 Check license compliance

#### Release (`release.yml`)
- 📦 Create GitHub releases
- 📦 Publish to PyPI
- 📦 Build Docker images
- 📦 Generate changelogs

#### PR Validation (`pr.yml`)
- 🏷️ Auto-label PRs
- 💬 Post coverage comments
- ✅ Enforce conventional commits
- 🔍 Review dependencies

### Local CI Commands

```bash
# Run all checks locally
make test-all

# Individual checks
make lint
make format
make type-check
make test
make coverage

# Fix issues
make format-fix
```

### CI/CD Documentation

- 📖 [Setup Guide](.github/SETUP_GUIDE.md) - 15-minute setup
- 📖 [Full Documentation](.github/CI_CD_DOCUMENTATION.md) - Complete reference
- 📊 [Workflow Diagrams](.github/WORKFLOW_DIAGRAM.md) - Visual overview

---

## 👨‍💻 Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/research-assistant.git
cd research-assistant

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
make verify
```

### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feat/your-feature
   ```

2. **Make changes**
   - Write code following style guide
   - Add tests for new features
   - Update documentation

3. **Run checks**
   ```bash
   make lint
   make test
   make type-check
   ```

4. **Commit changes**
   ```bash
   git commit -m "feat: add new feature"
   ```
   Follow [Conventional Commits](https://www.conventionalcommits.org/)

5. **Push and create PR**
   ```bash
   git push origin feat/your-feature
   ```

### Code Style

- **Formatting**: black (line length: 100)
- **Import sorting**: isort
- **Linting**: flake8, ruff
- **Type checking**: mypy (strict mode)
- **Docstrings**: Google style

Run formatters:
```bash
make format-fix
```

### Adding New Features

#### 1. Add a New Node

```python
# src/research_assistant/nodes/your_nodes.py
from src.research_assistant.core.state import YourState

def your_node(state: YourState) -> dict:
    """Your node description.
    
    Args:
        state: The current state
        
    Returns:
        Updated state dict
    """
    # Your logic here
    return {"key": "value"}
```

#### 2. Update Graph

```python
# src/research_assistant/graphs/your_graph.py
from langgraph.graph import StateGraph
from src.research_assistant.nodes.your_nodes import your_node

def build_your_graph() -> StateGraph:
    graph = StateGraph(YourState)
    graph.add_node("your_node", your_node)
    # Add edges...
    return graph.compile()
```

#### 3. Add Tests

```python
# tests/unit/test_your_nodes.py
def test_your_node(mock_llm):
    state = {"initial": "state"}
    result = your_node(state)
    assert result["key"] == "expected"
```

#### 4. Update Documentation

- Add docstrings
- Update README if needed
- Add usage examples

### Debugging

#### Enable Debug Logging

```python
import os
os.environ["LOG_LEVEL"] = "DEBUG"

from src.research_assistant.utils.logging import get_logger
logger = get_logger(__name__)
```

#### LangSmith Tracing

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_key
export LANGCHAIN_PROJECT=your_project
```

View traces at [smith.langchain.com](https://smith.langchain.com/)

#### Graph Visualization

```python
from src.research_assistant.graphs.research_graph import create_research_system

system = create_research_system(cfg)
system.get_graph().draw_mermaid_png(output_file="graph.png")
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Types of Contributions

- 🐛 **Bug reports**: Open an issue with details
- 💡 **Feature requests**: Describe your idea in an issue
- 📝 **Documentation**: Improve or fix documentation
- 🔧 **Code**: Submit pull requests
- 🧪 **Tests**: Add or improve test coverage
- 🌍 **Translations**: Help translate the interface

### Contribution Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feat/amazing-feature
   ```
3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation
4. **Run checks**
   ```bash
   make test-all
   ```
5. **Commit using conventional commits**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feat/amazing-feature
   ```
7. **Open a Pull Request**
   - Describe your changes
   - Reference any related issues
   - Wait for review

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks
- `ci:` CI/CD changes

Examples:
```bash
feat(search): add DuckDuckGo search provider
fix(report): correct citation formatting
docs: update installation instructions
test: add integration tests for interview graph
```

### Code Review Process

- All PRs require at least one approval
- CI checks must pass
- Code coverage should not decrease
- Follow style guidelines

### Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

✅ **Permitted:**
- Commercial use
- Modification
- Distribution
- Private use

❌ **Forbidden:**
- Liability
- Warranty

📋 **Required:**
- License and copyright notice

---

## 🙏 Acknowledgments

### Frameworks & Libraries

- **[LangChain](https://github.com/langchain-ai/langchain)**: LLM application framework
- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Graph-based workflow orchestration
- **[Pydantic](https://github.com/pydantic/pydantic)**: Data validation library
- **[Gradio](https://github.com/gradio-app/gradio)**: Web interface framework
- **[Hydra](https://github.com/facebookresearch/hydra)**: Configuration management

### Services

- **[OpenAI](https://openai.com/)**: GPT models
- **[Anthropic](https://www.anthropic.com/)**: Claude models
- **[Tavily](https://tavily.com/)**: Web search API

### Inspiration

- Research assistant patterns from academic literature
- Multi-agent system designs from AI research
- LangChain community examples and tutorials

### Contributors

Thanks to all contributors who have helped improve this project!

<!-- Generate contributor list automatically -->
<!-- <a href="https://github.com/yourusername/research-assistant/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yourusername/research-assistant" />
</a> -->

---

## 💬 Support

### Documentation

- 📖 **[Testing Guide](TESTING_GUIDE.md)**: Comprehensive testing documentation
- 📖 **[Type Checking Guide](TYPE_CHECKING_GUIDE.md)**: Type safety documentation
- 📖 **[CI/CD Setup](.github/SETUP_GUIDE.md)**: CI/CD configuration guide
- 📖 **[API Reference](docs/api.md)**: API documentation (coming soon)

### Getting Help

- 🐛 **Bug reports**: [Open an issue](https://github.com/yourusername/research-assistant/issues/new?template=bug_report.md)
- 💡 **Feature requests**: [Request a feature](https://github.com/yourusername/research-assistant/issues/new?template=feature_request.md)
- 💬 **Questions**: [GitHub Discussions](https://github.com/yourusername/research-assistant/discussions)
- 📧 **Email**: your.email@example.com

### Community

- 💬 **Discord**: [Join our server](https://discord.gg/your-server)
- 🐦 **Twitter**: [@your_handle](https://twitter.com/your_handle)
- 📺 **YouTube**: [Tutorial videos](https://youtube.com/your-channel)

### FAQ

**Q: How much does it cost to run?**
A: Costs depend on your LLM provider and usage. Budget-friendly configs available.

**Q: Can I use local LLMs?**
A: Yes! Use the `llm=local` configuration.

**Q: How long does research take?**
A: 2-5 minutes for 2-3 analysts, 5-8 minutes for 5 analysts.

**Q: Can I customize the report format?**
A: Yes, modify report templates in `src/research_assistant/prompts/report_prompts.py`.

**Q: Is there a hosted version?**
A: Not yet, but you can deploy it yourself using Docker or cloud platforms.

---

## 🚨 Status & Roadmap

### Current Status

🟢 **Active Development** - Version 0.1.0

**Note:** This project is in active development. Features, APIs, and documentation are subject to change. For questions, issues, or contributions, please open an issue or pull request on GitHub.

### Recent Updates

- ✅ Multi-agent research system
- ✅ Gradio web interface
- ✅ Comprehensive test suite
- ✅ CI/CD pipeline
- ✅ Type safety with mypy
- ✅ Structured logging

### Roadmap

#### v0.2.0 (Next Release)
- [ ] PDF export support
- [ ] Report templates
- [ ] Cost tracking
- [ ] Performance metrics dashboard

#### v0.3.0
- [ ] Database integration for history
- [ ] RAG enhancement
- [ ] Multi-language support
- [ ] Advanced citation management

#### v1.0.0
- [ ] Production-ready release
- [ ] Docker deployment
- [ ] API server
- [ ] Cloud hosting guide

### Contributing to Roadmap

Have ideas? [Open a feature request](https://github.com/yourusername/research-assistant/issues/new?template=feature_request.md)!

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/research-assistant?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/research-assistant?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/yourusername/research-assistant?style=social)

![GitHub issues](https://img.shields.io/github/issues/yourusername/research-assistant)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/research-assistant)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/research-assistant)
![GitHub contributors](https://img.shields.io/github/contributors/yourusername/research-assistant)

---

## 🎉 Ready to Get Started?

1. **Install the package**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Set up your environment**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

3. **Launch the web interface**
   ```bash
   python app/gradio_app.py
   ```

4. **Start researching!** 🔬

---

<div align="center">

**Built with ❤️ using LangChain and LangGraph**

[⭐ Star on GitHub](https://github.com/yourusername/research-assistant) | [🐛 Report Bug](https://github.com/yourusername/research-assistant/issues) | [💡 Request Feature](https://github.com/yourusername/research-assistant/issues)

</div>
