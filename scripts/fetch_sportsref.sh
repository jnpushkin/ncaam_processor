#!/bin/bash
# Fetch Sports Reference box scores for pending games
# Run daily via cron to auto-download when available

cd /Users/jeremypushkin/ncaam_processor

echo "=== Sports Reference Fetch: $(date) ==="

# Fetch any pending games
/usr/bin/python3 -m basketball_processor.scripts.fetch_sportsref

echo "=== Done ==="
echo ""
