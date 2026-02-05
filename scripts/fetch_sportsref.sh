#!/bin/bash
# Fetch Sports Reference box scores for pending games
# Then reprocess and deploy if any new games were fetched

cd /Users/jeremypushkin/ncaam_processor

# Use the correct Python 3.13 path
PYTHON3="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "=== Sports Reference Fetch: $(date) ==="

# Capture output to check if any games were fetched
OUTPUT=$($PYTHON3 -m basketball_processor.scripts.fetch_sportsref 2>&1)
echo "$OUTPUT"

# Check if any games were successfully fetched
if echo "$OUTPUT" | grep -q "SUCCESS!"; then
    echo ""
    echo "=== New games fetched - running processor ==="

    # Run processor (skip NBA checks to avoid rate limiting)
    $PYTHON3 -m basketball_processor --no-deploy --website-only 2>&1

    echo ""
    echo "=== Deploying to surge ==="

    # Deploy to surge
    /usr/bin/npx surge docs basketball-processor.surge.sh 2>&1

    echo ""
    echo "=== Deployment complete ==="
else
    echo ""
    echo "=== No new games fetched - skipping processor ==="
fi

echo ""
echo "=== Done: $(date) ==="
