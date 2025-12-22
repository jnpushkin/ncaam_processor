#!/bin/bash
# Weekly AP Poll Update Script
# Runs during basketball season (November - April) on Tuesdays
# AP polls are typically released on Monday, so Tuesday is ideal for scraping

set -e

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Log file
LOG_FILE="$PROJECT_DIR/logs/poll_updates.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if we're in basketball season (November - April)
MONTH=$(date +%m)
if [[ $MONTH -lt 4 || $MONTH -ge 11 ]]; then
    IN_SEASON=true
else
    IN_SEASON=false
fi

if [[ "$IN_SEASON" == "false" && "$1" != "--force" ]]; then
    log "Outside basketball season (May-October). Use --force to override."
    exit 0
fi

# Determine current season
YEAR=$(date +%Y)
if [[ $MONTH -ge 11 ]]; then
    SEASON="$YEAR-$(printf '%02d' $((YEAR % 100 + 1)))"
else
    PREV_YEAR=$((YEAR - 1))
    SEASON="$PREV_YEAR-$(printf '%02d' $((YEAR % 100)))"
fi

log "=== Starting poll update for $SEASON ==="

# Update men's polls
log "Updating men's polls..."
if python3 -m basketball_processor.scrapers.poll_scraper --season "$SEASON" --gender M 2>&1 | tee -a "$LOG_FILE"; then
    log "Men's polls updated successfully"
else
    log "ERROR: Failed to update men's polls"
fi

# Wait between requests (rate limiting)
sleep 5

# Update women's polls
log "Updating women's polls..."
if python3 -m basketball_processor.scrapers.poll_scraper --season "$SEASON" --gender W 2>&1 | tee -a "$LOG_FILE"; then
    log "Women's polls updated successfully"
else
    log "ERROR: Failed to update women's polls"
fi

log "=== Poll update complete ==="
