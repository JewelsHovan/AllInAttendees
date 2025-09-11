#!/bin/bash

##############################################################################
# Setup Cron Job for Daily All In 2025 Attendee Scraping
# 
# This script sets up a daily cron job to run the scraper
# Default: Runs at 2:00 AM every day
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default run time (2:00 AM)
DEFAULT_HOUR="2"
DEFAULT_MINUTE="0"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Daily Cron Job for All In Scraper${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Ask for run time
read -p "Enter hour to run daily (0-23) [default: ${DEFAULT_HOUR}]: " HOUR
HOUR=${HOUR:-$DEFAULT_HOUR}

read -p "Enter minute (0-59) [default: ${DEFAULT_MINUTE}]: " MINUTE
MINUTE=${MINUTE:-$DEFAULT_MINUTE}

# Validate input
if ! [[ "$HOUR" =~ ^[0-9]+$ ]] || [ "$HOUR" -lt 0 ] || [ "$HOUR" -gt 23 ]; then
    echo -e "${RED}Invalid hour: $HOUR${NC}"
    exit 1
fi

if ! [[ "$MINUTE" =~ ^[0-9]+$ ]] || [ "$MINUTE" -lt 0 ] || [ "$MINUTE" -gt 59 ]; then
    echo -e "${RED}Invalid minute: $MINUTE${NC}"
    exit 1
fi

# Create cron job entry
CRON_JOB="${MINUTE} ${HOUR} * * * cd ${SCRIPT_DIR} && /bin/bash ${SCRIPT_DIR}/run_daily_scrape.sh >> ${SCRIPT_DIR}/data/cron.log 2>&1"

echo ""
echo -e "${YELLOW}The following cron job will be added:${NC}"
echo "$CRON_JOB"
echo ""
echo -e "${YELLOW}This will run daily at ${HOUR}:$(printf '%02d' $MINUTE)${NC}"
echo ""

read -p "Do you want to add this cron job? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "run_daily_scrape.sh"; then
        echo -e "${YELLOW}Warning: A cron job for run_daily_scrape.sh already exists:${NC}"
        crontab -l | grep "run_daily_scrape.sh"
        echo ""
        read -p "Do you want to replace it? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Remove old cron job
            (crontab -l 2>/dev/null | grep -v "run_daily_scrape.sh") | crontab -
            echo -e "${GREEN}✓ Old cron job removed${NC}"
        else
            echo -e "${YELLOW}Keeping existing cron job${NC}"
            exit 0
        fi
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    echo -e "${GREEN}✓ Cron job added successfully!${NC}"
    echo ""
    echo -e "${BLUE}Current cron jobs:${NC}"
    crontab -l | grep "run_daily_scrape.sh" || echo "No cron jobs found"
    
    # Create log file if it doesn't exist
    mkdir -p "${SCRIPT_DIR}/data"
    touch "${SCRIPT_DIR}/data/cron.log"
    
    echo ""
    echo -e "${GREEN}Setup complete!${NC}"
    echo ""
    echo -e "${BLUE}The scraper will run daily at ${HOUR}:$(printf '%02d' $MINUTE)${NC}"
    echo -e "${BLUE}Logs will be saved to: ${SCRIPT_DIR}/data/cron.log${NC}"
    echo -e "${BLUE}Data will be saved to: ${SCRIPT_DIR}/data/runs/YYYY-MM-DD_HHMMSS/${NC}"
    echo ""
    echo -e "${YELLOW}To view cron logs:${NC}"
    echo "  tail -f ${SCRIPT_DIR}/data/cron.log"
    echo ""
    echo -e "${YELLOW}To list all cron jobs:${NC}"
    echo "  crontab -l"
    echo ""
    echo -e "${YELLOW}To remove the cron job:${NC}"
    echo "  crontab -l | grep -v 'run_daily_scrape.sh' | crontab -"
    
else
    echo -e "${YELLOW}Cron job not added${NC}"
fi