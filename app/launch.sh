# app/launch.sh
#!/bin/bash
# Launch script for Research Assistant Gradio App

set -e

echo "🚀 Launching Research Assistant Web UI..."

# Check if virtual environment exists
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
else
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        source venv/bin/activate
    fi
fi

# Check environment variables
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: No API keys found!"
    echo "Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
    exit 1
fi

# Create outputs directory
mkdir -p outputs
mkdir -p logs

# Launch the app
echo "✅ Starting Gradio app on http://localhost:7860"
python app/gradio_app.py "$@"
