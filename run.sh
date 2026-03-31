#!/bin/bash
# =============================================================================
# run.sh — Launch the AI Research Assistant
# =============================================================================
# Usage: bash run.sh
# Make executable: chmod +x run.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

echo "======================================"
echo "  AI Research Assistant"
echo "  Multi-Agent Debate System"
echo "======================================"
echo ""
echo "Starting Streamlit app..."
echo "Open http://localhost:8501 in your browser"
echo ""

# Launch the app
streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
