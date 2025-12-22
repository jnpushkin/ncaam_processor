#!/bin/bash
# Daily game sync script
# Downloads recent games for tracked teams

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

LOG_FILE="$PROJECT_DIR/logs/game_sync.log"
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

# Default to syncing last 2 days
DAYS=${1:-2}

log "=== Starting game sync (last $DAYS days) ==="

if python3 -m basketball_processor.scrapers.game_scraper --sync --days "$DAYS" 2>&1 | tee -a "$LOG_FILE"; then
    log "Game sync completed successfully"
else
    log "ERROR: Game sync failed"
fi

log "=== Game sync complete ==="
