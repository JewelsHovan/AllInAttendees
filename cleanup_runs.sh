#!/bin/bash

##############################################################################
# Cleanup utility for All In 2025 run directories
# 
# This script helps clean up incomplete or old run directories
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
echo -e "${BLUE}Run Directory Cleanup Utility${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a run is complete
is_run_complete() {
    local run_dir=$1
    
    # Check for essential files that indicate a complete run
    if [ -f "$run_dir/all_attendees.json" ] && [ -s "$run_dir/all_attendees.json" ] && \
       [ -f "$run_dir/all_attendees_with_details.csv" ] && [ -s "$run_dir/all_attendees_with_details.csv" ]; then
        return 0  # Complete
    else
        return 1  # Incomplete
    fi
}

# Function to get directory size
get_dir_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# Check if runs directory exists
if [ ! -d "data/runs" ]; then
    echo -e "${YELLOW}No runs directory found at data/runs${NC}"
    exit 0
fi

# Find all run directories
echo -e "${BLUE}Scanning run directories...${NC}"
echo ""

incomplete_count=0
complete_count=0
total_size_freed="0"

# Arrays to store directories
declare -a incomplete_dirs
declare -a old_complete_dirs

# Scan all directories in data/runs
for run_dir in data/runs/*/; do
    if [ -d "$run_dir" ] && [ "$run_dir" != "data/runs/latest/" ]; then
        dir_name=$(basename "$run_dir")
        dir_size=$(get_dir_size "$run_dir")
        
        if is_run_complete "$run_dir"; then
            # Check age of complete runs
            dir_age_days=$(( ($(date +%s) - $(stat -f %m "$run_dir" 2>/dev/null || stat -c %Y "$run_dir" 2>/dev/null)) / 86400 ))
            
            echo -e "${GREEN}✓ Complete:${NC} $dir_name (Size: $dir_size, Age: ${dir_age_days} days)"
            complete_count=$((complete_count + 1))
            
            # Mark old complete runs (optional cleanup)
            if [ $dir_age_days -gt 30 ]; then
                old_complete_dirs+=("$run_dir")
            fi
        else
            echo -e "${RED}✗ Incomplete:${NC} $dir_name (Size: $dir_size)"
            incomplete_dirs+=("$run_dir")
            incomplete_count=$((incomplete_count + 1))
        fi
    fi
done

echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  Complete runs: $complete_count"
echo "  Incomplete runs: $incomplete_count"
echo "  Old runs (>30 days): ${#old_complete_dirs[@]}"
echo ""

# Handle incomplete directories
if [ ${#incomplete_dirs[@]} -gt 0 ]; then
    echo -e "${YELLOW}Found ${#incomplete_dirs[@]} incomplete run(s)${NC}"
    read -p "Do you want to delete all incomplete runs? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for dir in "${incomplete_dirs[@]}"; do
            dir_size=$(get_dir_size "$dir")
            echo -e "  Deleting: $(basename "$dir") ($dir_size)..."
            rm -rf "$dir"
        done
        echo -e "${GREEN}✓ Deleted ${#incomplete_dirs[@]} incomplete run(s)${NC}"
    else
        echo -e "${YELLOW}Skipping incomplete run cleanup${NC}"
    fi
    echo ""
fi

# Handle old complete directories (optional)
if [ ${#old_complete_dirs[@]} -gt 0 ]; then
    echo -e "${YELLOW}Found ${#old_complete_dirs[@]} run(s) older than 30 days${NC}"
    read -p "Do you want to delete runs older than 30 days? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for dir in "${old_complete_dirs[@]}"; do
            dir_size=$(get_dir_size "$dir")
            echo -e "  Deleting: $(basename "$dir") ($dir_size)..."
            rm -rf "$dir"
        done
        echo -e "${GREEN}✓ Deleted ${#old_complete_dirs[@]} old run(s)${NC}"
    else
        echo -e "${YELLOW}Skipping old run cleanup${NC}"
    fi
    echo ""
fi

# Clean up any broken symlinks
if [ -L "data/runs/latest" ] && [ ! -e "data/runs/latest" ]; then
    echo -e "${YELLOW}Removing broken 'latest' symlink${NC}"
    rm -f "data/runs/latest"
    
    # Try to create a new symlink to the most recent complete run
    latest_complete=$(ls -td data/runs/*/ 2>/dev/null | grep -v "latest" | while read dir; do
        if is_run_complete "$dir"; then
            echo "$dir"
            break
        fi
    done)
    
    if [ -n "$latest_complete" ]; then
        ln -s "$(basename "$latest_complete")" "data/runs/latest"
        echo -e "${GREEN}✓ Created new 'latest' symlink to $(basename "$latest_complete")${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Cleanup complete!${NC}"

# Show current disk usage
echo ""
echo -e "${BLUE}Current disk usage:${NC}"
echo -n "  data/runs: "
get_dir_size "data/runs"
echo -n "  data/checkpoints: "
get_dir_size "data/checkpoints"