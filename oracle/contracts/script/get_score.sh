#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <PACKAGE_ID> <REGISTRY_ID>"
    echo ""
    echo "Query all WalletScore objects owned by the current Sui address."
    exit 1
fi

PACKAGE_ID=$1
REGISTRY_ID=$2

echo "Querying all WalletScore objects owned by current Sui address..."
echo ""

# Get current Sui address
SUI_ADDRESS=$(sui client active-address 2>/dev/null)

if [ -z "$SUI_ADDRESS" ]; then
    echo "Error: Failed to get active Sui address"
    exit 1
fi

# Query all WalletScore objects owned by this address
OWNED_OBJECTS=$(sui client objects --json 2>/dev/null | jq -r ".[] | select(.data.type == \"${PACKAGE_ID}::score_oracle::WalletScore\") | .data.objectId")

if [ -z "$OWNED_OBJECTS" ]; then
    echo "No WalletScore objects found for address: $SUI_ADDRESS"
    exit 0
fi

echo "=== WalletScore Objects Owned by $SUI_ADDRESS ==="
echo ""

# Fetch and display each score object
for OBJECT_ID in $OWNED_OBJECTS; do
    OBJECT_DATA=$(sui client object "$OBJECT_ID" --json 2>/dev/null)

    if [ $? -eq 0 ]; then
        SCORE=$(echo "$OBJECT_DATA" | jq -r '.content.fields.score')
        WALLET=$(echo "$OBJECT_DATA" | jq -r '.content.fields.wallet_address')
        TIMESTAMP=$(echo "$OBJECT_DATA" | jq -r '.content.fields.timestamp_ms')
        VERSION=$(echo "$OBJECT_DATA" | jq -r '.content.fields.version')

        echo "Object ID:   $OBJECT_ID"
        echo "Score:       $SCORE"
        echo "Wallet:      $WALLET"
        echo "Version:     $VERSION"
        echo "Timestamp:   $TIMESTAMP ms"
        echo "Date:        $(date -d @$((TIMESTAMP / 1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r $((TIMESTAMP / 1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'N/A')"
        echo ""
    fi
done
