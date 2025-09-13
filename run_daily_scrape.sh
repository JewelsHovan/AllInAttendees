#!/bin/bash

##############################################################################
# All In 2025 Attendee Data Collection Script
# 
# This script automates the daily collection of attendee data:
# 1. Scrapes all attendees
# 2. Fetches detailed information for each attendee
# 3. Reorganizes data with human-readable columns
#
# Output is organized by date in data/runs/YYYY-MM-DD_HHMMSS/
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Generate timestamp for this run
RUN_TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
export RUN_TIMESTAMP

# Create run directory and logs directory
RUN_DIR="data/runs/${RUN_TIMESTAMP}"
LOGS_DIR="${RUN_DIR}/logs"
mkdir -p "${LOGS_DIR}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}All In 2025 Attendee Data Collection${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Run timestamp: ${RUN_TIMESTAMP}${NC}"
echo -e "${YELLOW}Output directory: ${RUN_DIR}${NC}"
echo ""

# Function to handle errors
handle_error() {
    local script_name=$1
    local exit_code=$2
    echo -e "${RED}✗ Error: ${script_name} failed with exit code ${exit_code}${NC}"
    echo -e "${RED}Check log file: ${LOGS_DIR}/${script_name%.py}.log${NC}"
    
    # Clean up incomplete run
    echo -e "${YELLOW}Cleaning up incomplete run directory...${NC}"
    if [ -d "${RUN_DIR}" ]; then
        rm -rf "${RUN_DIR}"
        echo -e "${GREEN}✓ Cleaned up: ${RUN_DIR}${NC}"
    fi
    
    exit $exit_code
}

# Function to cleanup on exit
cleanup_on_exit() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ -d "${RUN_DIR}" ]; then
        echo -e "${YELLOW}Process interrupted. Cleaning up incomplete run...${NC}"
        
        # Check if we have any valid data files
        if [ ! -f "${RUN_DIR}/all_attendees.json" ] || [ ! -s "${RUN_DIR}/all_attendees.json" ]; then
            rm -rf "${RUN_DIR}"
            echo -e "${GREEN}✓ Cleaned up incomplete run: ${RUN_DIR}${NC}"
        else
            echo -e "${YELLOW}Keeping partial data in: ${RUN_DIR}${NC}"
        fi
    fi
}

# Set trap to cleanup on script exit
trap cleanup_on_exit EXIT

# Function to run a script with logging
run_script() {
    local script_name=$1
    local display_name=$2
    local log_file="${LOGS_DIR}/${script_name%.py}.log"
    
    echo -e "${BLUE}▶ Running ${display_name}...${NC}"
    
    # Run the script and capture output
    if python3 "$script_name" > "$log_file" 2>&1; then
        echo -e "${GREEN}✓ ${display_name} completed successfully${NC}"
        
        # Show summary from log
        if grep -q "Total attendees:" "$log_file" 2>/dev/null; then
            grep "Total attendees:" "$log_file" | tail -1
        fi
        if grep -q "Success:" "$log_file" 2>/dev/null; then
            grep "Success:" "$log_file" | tail -1
        fi
        if grep -q "Saved.*to:" "$log_file" 2>/dev/null; then
            grep "Saved.*to:" "$log_file" | tail -1
        fi
    else
        handle_error "$script_name" $?
    fi
    echo ""
}

# Check Python dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
python3 -c "import requests, pandas, json, csv" 2>/dev/null || {
    echo -e "${RED}Missing Python dependencies. Please install: pip install requests pandas${NC}"
    exit 1
}

# Check token validity
echo -e "${BLUE}Checking authentication token...${NC}"
if python3 refresh_token.py 2>&1 | grep -q "Token is valid"; then
    echo -e "${GREEN}✓ Authentication token is valid${NC}"
else
    echo -e "${RED}✗ Authentication token has expired or is invalid${NC}"
    echo -e "${YELLOW}Please update the token by following these steps:${NC}"
    echo "1. Open https://app.swapcard.com/event/all-in-2025/people"
    echo "2. Open Developer Tools (F12) > Network tab"
    echo "3. Refresh the page and find a GraphQL request"
    echo "4. Copy the 'authorization: Bearer ...' header"
    echo "5. Run: python3 refresh_token.py --update 'Bearer YOUR_NEW_TOKEN'"
    exit 1
fi

# Step 1: Scrape all attendees
echo -e "${YELLOW}Step 1/3: Scraping all attendees${NC}"
run_script "scrape_all_attendees_complete.py" "Attendee Scraper"

# Check if we got attendees
if [ ! -f "${RUN_DIR}/all_attendees.json" ]; then
    echo -e "${RED}✗ Error: No attendees file found at ${RUN_DIR}/all_attendees.json${NC}"
    echo -e "${YELLOW}Cleaning up incomplete run directory...${NC}"
    rm -rf "${RUN_DIR}"
    echo -e "${GREEN}✓ Cleaned up: ${RUN_DIR}${NC}"
    exit 1
fi

ATTENDEE_COUNT=$(python3 -c "import json; print(len(json.load(open('${RUN_DIR}/all_attendees.json'))))" 2>/dev/null || echo "0")
echo -e "${GREEN}Found ${ATTENDEE_COUNT} attendees${NC}"
echo ""

# Step 2: Fetch detailed information
echo -e "${YELLOW}Step 2/3: Fetching detailed information for each attendee${NC}"
echo -e "${YELLOW}This may take a while (approx. 20-30 minutes for ~2500 attendees)...${NC}"
run_script "batch_fetch_details.py" "Details Fetcher"

# Step 3: Reorganize and clean data
echo -e "${YELLOW}Step 3/3: Reorganizing and cleaning data${NC}"
run_script "reorganize_csv.py" "Data Organizer"

# Create symlink to latest run
echo -e "${BLUE}Creating symlink to latest run...${NC}"
rm -f data/runs/latest
ln -s "${RUN_TIMESTAMP}" data/runs/latest
echo -e "${GREEN}✓ Symlink created: data/runs/latest -> ${RUN_TIMESTAMP}${NC}"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Data collection completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Output files:${NC}"
echo "  • All attendees: ${RUN_DIR}/all_attendees.json"
echo "  • With details: ${RUN_DIR}/all_attendees_with_details.csv"
echo "  • Organized: ${RUN_DIR}/all_attendees_organized.csv"
echo "  • Excel-safe: ${RUN_DIR}/all_attendees_organized_excel_safe.csv"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  • ${LOGS_DIR}/"
echo ""

# Show file sizes
echo -e "${BLUE}File sizes:${NC}"
ls -lh "${RUN_DIR}"/*.{json,csv} 2>/dev/null | awk '{print "  • " $9 ": " $5}'

# Sync to database
echo ""
echo -e "${YELLOW}Step 4/4: Syncing to PostgreSQL database...${NC}"
if python3 "${SCRIPT_DIR}/database/sync_to_db.py" > "${LOGS_DIR}/database_sync.log" 2>&1; then
    echo -e "${GREEN}✓ Database sync completed successfully${NC}"
    # Show summary from database sync log
    if grep -q "Total attendees:" "${LOGS_DIR}/database_sync.log" 2>/dev/null; then
        grep "Total attendees:" "${LOGS_DIR}/database_sync.log" | tail -1
    fi
else
    echo -e "${RED}⚠️  Database sync failed (check ${LOGS_DIR}/database_sync.log)${NC}"
    echo -e "${YELLOW}Data collection completed but database not updated${NC}"
fi

# Optional: Clean up old runs (keep last 30 days)
if [ "${CLEANUP_OLD_RUNS:-false}" = "true" ]; then
    echo ""
    echo -e "${YELLOW}Cleaning up runs older than 30 days...${NC}"
    find data/runs -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup completed${NC}"
fi

echo ""
echo -e "${GREEN}Done! Run timestamp: ${RUN_TIMESTAMP}${NC}"