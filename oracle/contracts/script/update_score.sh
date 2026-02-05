#!/bin/bash

if [ $# -ne 5 ]; then
    echo "Usage: $0 <ENCLAVE_IP> <PACKAGE_ID> <ORACLE_ID> <ENCLAVE_ID> <ADDRESS>"
    exit 1
fi

ENCLAVE_IP=$1
PACKAGE_ID=$2
ORACLE_ID=$3
ENCLAVE_ID=$4
ADDRESS=$5

# Fetch signed score from enclave
RESPONSE=$(curl -s "http://${ENCLAVE_IP}:3000/score?address=${ADDRESS}")

if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch score from enclave"
    exit 1
fi

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
    echo "Error: Invalid JSON response from enclave"
    echo "Response: $RESPONSE"
    exit 1
fi

SCORE=$(echo $RESPONSE | jq -r '.score')
WALLET_ADDRESS=$(echo $RESPONSE | jq -r '.wallet_address')
TIMESTAMP_MS=$(echo $RESPONSE | jq -r '.timestamp_ms')
SIGNATURE=$(echo $RESPONSE | jq -r '.signature')

echo "Score:  $SCORE"
echo "Wallet: $WALLET_ADDRESS"
echo "Timestamp: $TIMESTAMP_MS"
echo "Signature: ${SIGNATURE:0:20}...${SIGNATURE: -20}"

# Convert wallet address string to vector<u8> format for Move
WALLET_VECTOR=$(python3 -c "
addr = '$WALLET_ADDRESS'
bytes = [ord(c) for c in addr]
print('[' + ','.join(map(str, bytes)) + ']')
")

# Convert hex signature to vector format for Move
SIG_VECTOR=$(python3 -c "
sig = '$SIGNATURE'
bytes = [int(sig[i:i+2], 16) for i in range(0, len(sig), 2)]
print('[' + ','.join(map(str, bytes)) + ']')
")

echo "Wallet Vector: ${WALLET_VECTOR:0:40}...]"
echo "Signature Vector: ${SIG_VECTOR:0:30}...]"

sui client call \
  --package $PACKAGE_ID \
  --module score_oracle \
  --function update_wallet_score \
  --args "$ORACLE_ID" "$ENCLAVE_ID" "$SCORE" "$WALLET_VECTOR" "$TIMESTAMP_MS" "$SIG_VECTOR" \
  --gas-budget 10000000
