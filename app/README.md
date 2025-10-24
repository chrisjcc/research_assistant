# app/README.md
# Research Assistant Web UI

Interactive web interface for the AI Research Assistant built with Gradio.

## Features

- 🎯 **Simple Interface**: Easy-to-use web UI for running research
- 👥 **Analyst Review**: Review and approve AI-generated analyst personas
- 📊 **Progress Tracking**: Real-time progress updates during research
- 💾 **Report Download**: Download complete research reports in Markdown
- 🔄 **Feedback Loop**: Provide feedback to regenerate analysts

## Quick Start

### Option 1: Using Launch Script (Recommended)

```bash
# Linux/Mac
chmod +x app/launch.sh
./app/launch.sh

# Windows
app\launch.bat
```

### Option 2: Manual Launch

```bash
# Install dependencies
pip install -e ".[dev]"

# Set API keys
export OPENAI_API_KEY="your-key-here"
export TAVILY_API_KEY="your-key-here"

# Run the app
python app/gradio_app.py
```

### Option 3: With Custom Settings

```bash
# Custom port
python app/gradio_app.py --port 8080

# Create public share link
python app/gradio_app.py --share

# Debug mode
python app/gradio_app.py --debug
```

## Usage

1. **Enter Research Topic**: Describe what you want to research
2. **Configure Parameters**:
   - Number of analysts (1-10)
   - Interview depth (1-5 turns)
   - Optional detailed prompts
3. **Generate Analysts**: Click "Start Research" to create analyst personas
4. **Review Analysts**: Examine the generated analysts
5. **Approve or Provide Feedback**:
   - Type "approve" to continue
   - Or provide specific feedback to regenerate
6. **Wait for Completion**: Monitor progress as analysts conduct research
7. **Download Report**: Save your comprehensive research report

## Example Topics

- "AI Safety and Alignment"
- "Quantum Computing Applications in Drug Discovery"
- "Climate Change Mitigation Technologies"
- "Large Language Models: Capabilities and Limitations"
- "Renewable Energy Storage Solutions"

## Configuration

The app uses the main research assistant configuration from `config/default.yaml`.

To customize:

```bash
# Copy default config
cp config/default.yaml config/my_config.yaml

# Edit your config
vim config/my_config.yaml

# Use custom config
export RESEARCH_CONFIG=config/my_config.yaml
python app/gradio_app.py
```

## Troubleshooting

### API Key Errors

```bash
# Check if keys are set
echo $OPENAI_API_KEY
echo $TAVILY_API_KEY

# Set keys if missing
export OPENAI_API_KEY="sk-..."
export TAVILY_API_KEY="tvly-..."
```

### Port Already in Use

```bash
# Use different port
python app/gradio_app.py --port 8080
```

### Graph Initialization Fails

- Check that all dependencies are installed: `pip install -e ".[dev]"`
- Verify API keys are valid
- Check logs in `logs/` directory

## Development

### Running in Debug Mode

```bash
python app/gradio_app.py --debug
```

### Viewing Logs

```bash
# Application logs
tail -f logs/app.log

# Research logs
tail -f logs/research.log
```

### Customizing the UI

Edit `app/gradio_app.py` to customize:
- UI layout and styling
- Progress tracking
- Report formatting
- Download options

## Architecture

```
User Interface (Gradio)
    ↓
Research Graph (LangGraph)
    ↓
┌─────────────┬──────────────┬─────────────┐
│  Analysts   │  Interviews  │   Report    │
│  Creation   │  Execution   │  Synthesis  │
└─────────────┴──────────────┴─────────────┘
    ↓
Final Report (Markdown)
```

## API

The Gradio app provides these main functions:

- `start_research()`: Initialize and create analysts
- `approve_analysts()`: Continue with approved analysts
- `regenerate_analysts()`: Regenerate with feedback

## Performance

Typical execution times:
- **2 analysts**: 2-3 minutes
- **3 analysts**: 3-5 minutes
- **5 analysts**: 5-8 minutes

Times vary based on:
- Interview depth (turns per interview)
- Topic complexity
- API response times

## Deployment

### Local Deployment

Already covered above with launch scripts.

### Docker Deployment

```bash
# Build image
docker build -t research-assistant .

# Run container
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e TAVILY_API_KEY=$TAVILY_API_KEY \
  research-assistant
```

### Cloud Deployment (Hugging Face Spaces)

1. Create a new Space on Hugging Face
2. Upload the app files
3. Set environment variables in Space settings
4. Deploy!

## License

See main project LICENSE file.

## Support

For issues or questions:
- Check the main project README
- Review logs in `logs/` directory
- Open an issue on GitHub
