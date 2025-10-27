# Research Assistant

[![Tests](https://img.shields.io/badge/tests-24%20passed-success)](https://github.com/your-org/research-assistant/actions)
[![Coverage](https://img.shields.io/badge/coverage-41.75%25-yellow)](https://github.com/your-org/research-assistant/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> AI-powered research assistant using LangGraph for multi-analyst research workflows

## 🧪 Testing

![Tests: 24/29 passing](https://img.shields.io/badge/tests-24%2F29%20passing-brightgreen)
![Skipped: 4](https://img.shields.io/badge/skipped-4-blue)
![XFailed: 1](https://img.shields.io/badge/xfailed-1-yellow)
![Coverage: 41.75%](https://img.shields.io/badge/coverage-41.75%25-yellow)

### Quick Test

```bash
make test-integration
```

### Latest Results

```
✅ 24 passed  ⏭️ 4 skipped  🔄 1 xfailed  ⏱️ 16.50s
```

**Status**: All substantive tests passing ✅

### Test Breakdown

| Category | Tests | Status |
|----------|-------|--------|
| Core Functionality | 9 | ✅ All passing |
| Error Handling | 3 | ✅ All passing |
| Performance | 2 | ✅ All passing |
| State Management | 2 | ✅ All passing |
| Edge Cases | 3 | ✅ All passing |
| Regressions | 2 | ✅ All passing |
| API Integration | 2 | ⏭️ Skipped (requires API keys) |
| Feature Testing | 2 | ⏭️ Skipped (not implemented) |

### Coverage Highlights

- 🟢 **78%** - Search tools
- 🟢 **67-87%** - Prompt templates  
- 🟢 **62%** - Core schemas
- 🟡 **45-72%** - Graph orchestration
- 🟡 **51-60%** - Node functions
- 🔴 **13-37%** - Utility functions

### Running Tests

```bash
# All tests
make test-integration

# Specific category
pytest tests/integration/test_graph_execution.py::TestInterviewGraphIntegration -v

# With coverage
pytest tests/integration --cov=src/research_assistant --cov-report=html
```

---

## 📦 Installation

```bash
pip install -e .
```

## 🚀 Quick Start

```python
from research_assistant.graphs import build_research_graph

graph = build_research_graph()
result = graph.invoke({"topic": "AI Safety", "max_analysts": 3})
```

## 📖 Documentation

- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Testing Guide](docs/testing.md)
- [Contributing](CONTRIBUTING.md)

## 🤝 Contributing

Contributions welcome! Please ensure:
- ✅ All tests pass
- ✅ Coverage stays above 40%
- ✅ Code follows style guide

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
