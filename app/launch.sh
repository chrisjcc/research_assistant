# app/launch.sh
#!/bin/bash
# Launch script for Research Assistant Gradio App

set -e

echo "🚀 Launching Research Assistant Web UI..."

# Ensure environment is active
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  Not in Conda env. Please activate 'research-assistant' first:"
    echo "   conda activate research-assistant"
    exit 1
else
    echo "✅ Using Conda environment: $CONDA_DEFAULT_ENV"
fi

# Check API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: No API keys found!"
    exit 1
fi

# Create outputs directory
mkdir -p outputs logs

# Launch the app
echo "✅ Starting Gradio app on http://localhost:7860"
python app/gradio_app.py "$@"
