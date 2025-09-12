#!/bin/bash

##############################################################################
# Launch script for All In 2025 Analytics Dashboard
##############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}All In 2025 Analytics Dashboard${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}Streamlit not found. Installing required packages...${NC}"
    pip3 install -r streamlit_app/requirements.txt
    echo ""
fi

# Check if data exists
if [ ! -d "data/runs" ] || [ -z "$(ls -A data/runs 2>/dev/null)" ]; then
    echo -e "${RED}No data runs found in data/runs/${NC}"
    echo -e "${YELLOW}Please run ./run_daily_scrape.sh first to collect data${NC}"
    exit 1
fi

# Get port from argument or use default
PORT=${1:-8501}

echo -e "${GREEN}Starting Streamlit app on port ${PORT}...${NC}"
echo -e "${YELLOW}Open your browser at: http://localhost:${PORT}${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

# Run streamlit from project root
streamlit run streamlit_app/app.py --server.port=$PORT