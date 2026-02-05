#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <PACKAGE_ID> <ORACLE_ID>"
    exit 1
fi

PACKAGE_ID=$1
ORACLE_ID=$2

echo "Querying score oracle on-chain state..."
echo ""

# Get the oracle object data
ORACLE_DATA=$(sui client object "$ORACLE_ID" --json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch oracle object"
    exit 1
fi

# Extract latest score data from the object fields
LATEST_SCORE=$(echo "$ORACLE_DATA" | jq -r '.content.fields.latest_score')
LATEST_WALLET=$(echo "$ORACLE_DATA" | jq -r '.content.fields.latest_wallet_address')
LATEST_TIMESTAMP=$(echo "$ORACLE_DATA" | jq -r '.content.fields.latest_timestamp')

if [ -z "$LATEST_SCORE" ] || [ "$LATEST_SCORE" = "null" ]; then
    echo "Error: Could not parse oracle data"
    echo "Raw data:"
    echo "$ORACLE_DATA" | jq
    exit 1
fi

# Check if any score has been recorded
if [ "$LATEST_TIMESTAMP" = "0" ]; then
    echo "No scores recorded yet in the oracle."
    exit 0
fi

echo "=== Latest Score Data ==="
echo "Score:       $LATEST_SCORE"
echo "Wallet:      $LATEST_WALLET"
echo "Timestamp:   $LATEST_TIMESTAMP ms"
echo "Date:        $(date -d @$((LATEST_TIMESTAMP / 1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r $((LATEST_TIMESTAMP / 1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'N/A')"
echo ""
