#!/bin/bash
set -e

echo "=== Oyster CVM Automated Deployment ==="
echo ""

# Check prerequisites
if [ -z "$PRIVATE_KEY" ]; then
    echo "Error: PRIVATE_KEY environment variable is not set"
    exit 1
fi

if ! command -v sui &> /dev/null; then
    echo "Error: sui CLI not found"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: docker not found"
    exit 1
fi

if ! command -v oyster-cvm &> /dev/null; then
    echo "Error: oyster-cvm CLI not found"
    exit 1
fi

# Constants
AWS_INSTANCE=c6a.2xlarge

# Store deployment info
DEPLOYMENT_FILE="deployment.env"
rm -f "$DEPLOYMENT_FILE"

echo "Step 1: Deploy Smart Contracts"
echo "==============================="
cd contracts

echo "Building contracts..."
sui move build

echo "Publishing contracts..."
PUBLISH_OUTPUT=$(sui client publish --gas-budget 100000000 --with-unpublished-dependencies 2>&1)

echo "$PUBLISH_OUTPUT"

# Parse PACKAGE_ID from Published Objects section
PACKAGE_ID=$(echo "$PUBLISH_OUTPUT" | grep "PackageID:" | sed 's/.*PackageID: //' | sed 's/[│ ]//g' | head -1)

# Parse ENCLAVE_CONFIG_ID (Shared object with EnclaveConfig type)
ENCLAVE_CONFIG_ID=$(echo "$PUBLISH_OUTPUT" | grep -B 3 "enclave::EnclaveConfig" | grep "ObjectID:" | sed 's/.*ObjectID: //' | sed 's/[│ ]//g')

# Parse CAP_ID (owned object with Cap type)
CAP_ID=$(echo "$PUBLISH_OUTPUT" | grep -B 3 "enclave::Cap" | grep "ObjectID:" | sed 's/.*ObjectID: //' | sed 's/[│ ]//g')

# Validate extraction
if [ -z "$PACKAGE_ID" ] || [ -z "$ENCLAVE_CONFIG_ID" ] || [ -z "$CAP_ID" ]; then
    echo "Error: Failed to extract object IDs from deployment output"
    echo "PACKAGE_ID: $PACKAGE_ID"
    echo "ENCLAVE_CONFIG_ID: $ENCLAVE_CONFIG_ID"
    echo "CAP_ID: $CAP_ID"
    exit 1
fi

echo ""
echo "Successfully extracted deployment IDs:"
echo "  PACKAGE_ID:        $PACKAGE_ID"
echo "  ENCLAVE_CONFIG_ID: $ENCLAVE_CONFIG_ID"
echo "  CAP_ID:            $CAP_ID"

# Save to deployment file
cat > "../$DEPLOYMENT_FILE" << EOF
PACKAGE_ID=$PACKAGE_ID
ENCLAVE_CONFIG_ID=$ENCLAVE_CONFIG_ID
CAP_ID=$CAP_ID
EOF

echo ""
echo "Deployment info saved to $DEPLOYMENT_FILE"
echo ""
echo "=== Step 1 Complete ==="

cd ..

echo ""
echo "Step 2: Build and Deploy Enclave (Node.js)"
echo "==========================================="

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    BUILD_ARCH="amd64"
    IMAGE_TAG="node-reproducible-amd64"
    IMAGE_FILE="./node-amd64-image.tar.gz"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    BUILD_ARCH="arm64"
    IMAGE_TAG="node-reproducible-arm64"
    IMAGE_FILE="./node-arm64-image.tar.gz"
else
    echo "Error: Unsupported architecture: $ARCH"
    exit 1
fi

echo "Detected architecture: $ARCH (building for $BUILD_ARCH)"

# Check for Docker registry username
if [ -z "$DOCKER_REGISTRY" ]; then
    echo ""
    echo "Docker registry username not set."
    read -p "Enter your Docker Hub username (or registry): " DOCKER_REGISTRY
    if [ -z "$DOCKER_REGISTRY" ]; then
        echo "Error: Docker registry username is required"
        exit 1
    fi
fi

echo ""
echo "Building enclave with Nix..."
./nix.sh build-node-$BUILD_ARCH

if [ ! -f "$IMAGE_FILE" ]; then
    echo "Error: Build failed, image file not found: $IMAGE_FILE"
    exit 1
fi

echo "Loading Docker image..."
docker load < "$IMAGE_FILE"

# Tag and push
FULL_IMAGE_NAME="$DOCKER_REGISTRY/evm-score-oracle:$IMAGE_TAG"
echo ""
echo "Tagging image as: $FULL_IMAGE_NAME"
docker tag "evm-score-oracle:$IMAGE_TAG" "$FULL_IMAGE_NAME"

echo "Pushing to registry..."
docker push "$FULL_IMAGE_NAME"

# Get digest
echo "Extracting image digest..."
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$FULL_IMAGE_NAME")

if [ -z "$DIGEST" ]; then
    echo "Error: Failed to get image digest"
    exit 1
fi

echo "Image digest: $DIGEST"

# Update docker-compose.yml
echo "Updating app/docker-compose.yml with digest..."
sed -i "/^  evm-score-oracle:/,/^[^ ]/ { /^    image:/ s|^    image:.*|    image: $DIGEST| }" app/docker-compose.yml

echo ""
echo "Deploying to Oyster..."

# Deploy with oyster-cvm
DEPLOY_OUTPUT=$(oyster-cvm deploy \
    --wallet-private-key "$PRIVATE_KEY" \
    --docker-compose ./app/docker-compose.yml \
    --instance-type $AWS_INSTANCE \
    --duration-in-minutes 60 \
    --arch amd64 \
    --deployment sui 2>&1)

echo "$DEPLOY_OUTPUT"

# Parse OYSTER_JOB_ID from output
JOB_ID=$(echo "$DEPLOY_OUTPUT" | grep -oP 'Job created with ID: "\K[0-9]+' | head -1)

if [ -z "$JOB_ID" ]; then
    echo ""
    echo "Warning: Could not extract JOB_ID from output"
fi

# Parse PUBLIC_IP from output
PUBLIC_IP=$(echo "$DEPLOY_OUTPUT" | grep -oP 'PUBLIC_IP=\K[0-9.]+' | head -1)

if [ -z "$PUBLIC_IP" ]; then
    # Try alternative pattern: IP address: x.x.x.x
    PUBLIC_IP=$(echo "$DEPLOY_OUTPUT" | grep -oP 'IP address:\s+\K[0-9.]+' | head -1)
fi

if [ -z "$PUBLIC_IP" ]; then
    # Try JSON pattern: {"ip":"x.x.x.x"}
    PUBLIC_IP=$(echo "$DEPLOY_OUTPUT" | grep -oP '{"ip":"\K[0-9.]+' | head -1)
fi

if [ -z "$PUBLIC_IP" ]; then
    echo ""
    echo "Warning: Could not automatically extract PUBLIC_IP from output"
    read -p "Enter the PUBLIC_IP from the deployment output: " PUBLIC_IP
fi

# Validate PUBLIC_IP
if [ -z "$PUBLIC_IP" ]; then
    echo "Error: PUBLIC_IP is required"
    exit 1
fi

echo ""
echo "Enclave deployed successfully!"
echo "  JOB_ID: $JOB_ID"
echo "  PUBLIC_IP: $PUBLIC_IP"

# Append to deployment file
cat >> "$DEPLOYMENT_FILE" << EOF
JOB_ID=$JOB_ID
PUBLIC_IP=$PUBLIC_IP
DIGEST=$DIGEST
EOF

echo ""
echo "=== Step 2 Complete ==="

echo ""
echo "Step 3: Register Enclave On-Chain"
echo "=================================="

# Load deployment variables
source "$DEPLOYMENT_FILE"

# Note: Both enclave and oyster_demo modules are in the same package
ENCLAVE_PACKAGE_ID="$PACKAGE_ID"

echo "Waiting for enclave to be ready..."
sleep 10

# Test enclave health
echo "Testing enclave health endpoint..."
if ! curl -sf "http://${PUBLIC_IP}:3000/health" > /dev/null; then
    echo "Warning: Enclave health check failed. Waiting 20 more seconds..."
    sleep 20
fi

echo "Waiting for Ollama to be ready..."
MAX_OLLAMA_RETRIES=30
OLLAMA_RETRY_COUNT=0
while [ $OLLAMA_RETRY_COUNT -lt $MAX_OLLAMA_RETRIES ]; do
    HEALTH_RESPONSE=$(curl -sf "http://${PUBLIC_IP}:3000/health" 2>/dev/null || echo "{}")
    OLLAMA_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"ollama":"connected"' || echo "")
    if [ -n "$OLLAMA_STATUS" ]; then
        echo "Ollama is ready and connected!"
        break
    fi
    OLLAMA_RETRY_COUNT=$((OLLAMA_RETRY_COUNT + 1))
    echo "Ollama not ready yet (attempt $OLLAMA_RETRY_COUNT/$MAX_OLLAMA_RETRIES)..."
    sleep 10
done

if [ $OLLAMA_RETRY_COUNT -eq $MAX_OLLAMA_RETRIES ]; then
    echo "Warning: Ollama health check timeout after ${MAX_OLLAMA_RETRIES} attempts"
    echo "Service may still work with fallback scoring"
fi

echo ""
echo "Getting attestation from enclave..."
ATTESTATION_HEX=$(curl -s "http://${PUBLIC_IP}:1301/attestation/hex")

if [ -z "$ATTESTATION_HEX" ]; then
    echo "Error: Failed to get attestation from enclave"
    exit 1
fi

echo "Attestation received (length: ${#ATTESTATION_HEX} chars)"

echo ""
echo "Getting PCR values from enclave..."
VERIFY_OUTPUT=$(oyster-cvm verify --enclave-ip "$PUBLIC_IP" 2>&1)

echo "$VERIFY_OUTPUT"

# Extract PCR values
PCR0=$(echo "$VERIFY_OUTPUT" | grep -oP 'PCR0:\s*\K[a-f0-9]+' | head -1)
PCR1=$(echo "$VERIFY_OUTPUT" | grep -oP 'PCR1:\s*\K[a-f0-9]+' | head -1)
PCR2=$(echo "$VERIFY_OUTPUT" | grep -oP 'PCR2:\s*\K[a-f0-9]+' | head -1)
PCR16=$(echo "$VERIFY_OUTPUT" | grep -oP 'PCR16:\s*\K[a-f0-9]+' | head -1)

# Validate PCR extraction
if [ -z "$PCR0" ] || [ -z "$PCR1" ] || [ -z "$PCR2" ] || [ -z "$PCR16" ]; then
    echo ""
    echo "Error: Failed to extract PCR values from verification output"
    echo "PCR0: $PCR0"
    echo "PCR1: $PCR1"
    echo "PCR2: $PCR2"
    echo "PCR16: $PCR16"
    exit 1
fi

echo ""
echo "Successfully extracted PCR values:"
echo "  PCR0:  $PCR0"
echo "  PCR1:  $PCR1"
echo "  PCR2:  $PCR2"
echo "  PCR16: $PCR16"

echo ""
echo "Updating PCRs in contract..."
UPDATE_PCR_OUTPUT=$(sui client call \
    --package "$ENCLAVE_PACKAGE_ID" \
    --module enclave \
    --function update_pcrs \
    --args "$ENCLAVE_CONFIG_ID" "$CAP_ID" "0x${PCR0}" "0x${PCR1}" "0x${PCR2}" "0x${PCR16}" \
    --type-args "${PACKAGE_ID}::score_oracle::SCORE_ORACLE" \
    --gas-budget 10000000 2>&1)

echo "$UPDATE_PCR_OUTPUT"

if echo "$UPDATE_PCR_OUTPUT" | grep -q "Status: Success"; then
    echo "PCRs updated successfully"
else
    echo "Error: Failed to update PCRs"
    exit 1
fi

echo ""
echo "Registering enclave..."
cd contracts/script

REGISTER_OUTPUT=$(bash register_enclave.sh \
    "$ENCLAVE_PACKAGE_ID" \
    "$PACKAGE_ID" \
    "$ENCLAVE_CONFIG_ID" \
    "$PUBLIC_IP" \
    score_oracle \
    SCORE_ORACLE 2>&1)

echo "$REGISTER_OUTPUT"

cd ../..

# Extract ENCLAVE_ID from the registration output
ENCLAVE_ID=$(echo "$REGISTER_OUTPUT" | grep -oP 'ObjectID:\s*\K0x[a-f0-9]+' | grep -v "$ENCLAVE_CONFIG_ID" | head -1)

if [ -z "$ENCLAVE_ID" ]; then
    echo ""
    echo "Warning: Could not automatically extract ENCLAVE_ID from output"
    read -p "Enter the ENCLAVE_ID from the registration output: " ENCLAVE_ID
fi

# Validate ENCLAVE_ID
if [ -z "$ENCLAVE_ID" ]; then
    echo "Error: ENCLAVE_ID is required"
    exit 1
fi

echo ""
echo "Enclave registered successfully!"
echo "  ENCLAVE_ID: $ENCLAVE_ID"

# Append to deployment file
cat >> "$DEPLOYMENT_FILE" << EOF
ENCLAVE_PACKAGE_ID=$ENCLAVE_PACKAGE_ID
PCR0=$PCR0
PCR1=$PCR1
PCR2=$PCR2
PCR16=$PCR16
ENCLAVE_ID=$ENCLAVE_ID
EOF

echo ""
echo "=== Step 3 Complete ==="

echo ""
echo "Step 4: Initialize Oracle"
echo "========================="

# Load deployment variables
source "$DEPLOYMENT_FILE"

echo "Initializing oracle contract..."
cd contracts/script

INIT_OUTPUT=$(bash initialize_oracle.sh "$PACKAGE_ID" 2>&1)

echo "$INIT_OUTPUT"

cd ../..

# Extract REGISTRY_ID (shared object with ScoreRegistry type)
REGISTRY_ID=$(echo "$INIT_OUTPUT" | grep -B 3 "ScoreRegistry" | grep "ObjectID:" | sed 's/.*ObjectID: //' | sed 's/[│ ]//g' | head -1)

if [ -z "$REGISTRY_ID" ]; then
    # Alternative: look for "Shared(" in Created Objects section
    REGISTRY_ID=$(echo "$INIT_OUTPUT" | grep -A 10 "Created Objects:" | grep -B 3 "Shared(" | grep "ObjectID:" | sed 's/.*ObjectID: //' | sed 's/[│ ]//g' | head -1)
fi

if [ -z "$REGISTRY_ID" ]; then
    echo ""
    echo "Warning: Could not automatically extract REGISTRY_ID from output"
    read -p "Enter the REGISTRY_ID (shared ScoreRegistry object) from the output: " REGISTRY_ID
fi

# Validate REGISTRY_ID
if [ -z "$REGISTRY_ID" ]; then
    echo "Error: REGISTRY_ID is required"
    exit 1
fi

echo ""
echo "Registry initialized successfully!"
echo "  REGISTRY_ID: $REGISTRY_ID"

# Append to deployment file
cat >> "$DEPLOYMENT_FILE" << EOF
REGISTRY_ID=$REGISTRY_ID
EOF

echo ""
echo "=== Step 4 Complete ==="

echo ""
echo "Step 5: Update Score (Initial)"
echo "==============================="

# Load deployment variables
source "$DEPLOYMENT_FILE"

echo "Fetching and submitting initial score..."
cd contracts/script

TEST_ADDRESS="0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba"
UPDATE_OUTPUT=$(bash update_score.sh "$PUBLIC_IP" "$PACKAGE_ID" "$REGISTRY_ID" "$ENCLAVE_ID" "$TEST_ADDRESS" 2>&1)

echo "$UPDATE_OUTPUT"

cd ../..

if echo "$UPDATE_OUTPUT" | grep -q "Status: Success"; then
    echo ""
    echo "Score updated successfully!"
else
    echo ""
    echo "Warning: Score update may have failed. Check output above."
fi

echo ""
echo "=== Step 5 Complete ==="

echo ""
echo "=========================================="
echo "=== DEPLOYMENT COMPLETED SUCCESSFULLY ==="
echo "=========================================="
echo ""
echo "Deployment summary saved to: $DEPLOYMENT_FILE"
echo ""
cat "$DEPLOYMENT_FILE"
echo ""
echo "You can now:"
echo "  - Query score: cd contracts/script && sh get_score.sh $PACKAGE_ID $REGISTRY_ID"
echo "  - Update score: cd contracts/script && sh update_score.sh $PUBLIC_IP $PACKAGE_ID $REGISTRY_ID $ENCLAVE_ID <ADDRESS>"
echo ""
