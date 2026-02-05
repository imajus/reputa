# EVM Transaction Score Oracle

A Trusted Execution Environment (TEE) oracle that fetches EVM transaction data and stores verified scores on the Sui blockchain.

## Architecture

### Components

1. **Smart Contracts** (`contracts/`)
   - `score_oracle.move` - Main oracle contract that stores wallet scores with signature verification
   - `enclave.move` - Enclave attestation and registration module

2. **Node.js Enclave** (`app/`)
   - Fetches transaction counts from n8n webhook API
   - Signs score data with secp256k1 inside TEE
   - Exposes HTTP endpoints for score queries

3. **Deployment Scripts**
   - `deploy.sh` - Automated deployment to Oyster CVM
   - `nix.sh` - Reproducible Docker image building with Nix

## Data Flow

```
User Query → Enclave API → n8n Webhook → EVM Transaction Data
                ↓
         Calculate Score (tx count)
                ↓
         Sign with TEE Key
                ↓
    Store on Sui with Signature Verification
```

## API Endpoints

### Enclave Service (Port 3000)

- `GET /health` - Health check
- `GET /public-key` - Get enclave's compressed secp256k1 public key
- `GET /score?address=0x...` - Get signed score for EVM address

Example response:
```json
{
  "score": 37,
  "wallet_address": "0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba",
  "timestamp_ms": 1738742400000,
  "signature": "a1b2c3..."
}
```

### Smart Contract Functions

- `initialize_oracle()` - Create and share ScoreOracle object
- `update_wallet_score()` - Submit signed score to blockchain
- `get_latest_score()` - Query latest score `(score, address, timestamp)`
- `get_score_at_timestamp()` - Historical score lookup

## Deployment

### Prerequisites

- Sui CLI v1.35+
- Docker v29+
- Oyster CVM CLI
- Nix with flakes enabled
- Sui wallet with testnet funds

### Quick Start

```bash
# Set private key for deployment
export PRIVATE_KEY="your_sui_private_key"
export DOCKER_REGISTRY="your_dockerhub_username"

# Run automated deployment
./deploy.sh
```

The script will:
1. Build and publish smart contracts
2. Build enclave Docker image with Nix
3. Deploy to Oyster CVM
4. Register enclave with attestation
5. Initialize oracle
6. Submit test score

### Manual Steps

#### 1. Build Contracts
```bash
cd contracts
sui move build
sui client publish --gas-budget 100000000 --with-unpublished-dependencies
```

#### 2. Build Enclave
```bash
# For ARM64 (Apple Silicon, AWS Graviton)
./nix.sh build-node-arm64

# For AMD64 (x86_64)
./nix.sh build-node-amd64
```

#### 3. Deploy to Oyster
```bash
cd app
oyster-cvm deploy \
  --wallet-private-key "$PRIVATE_KEY" \
  --docker-compose ./docker-compose.yml \
  --instance-type c6a.xlarge \
  --duration-in-minutes 60 \
  --arch amd64 \
  --deployment sui
```

#### 4. Register Enclave
```bash
cd contracts/script
./register_enclave.sh <ENCLAVE_PACKAGE_ID> <PACKAGE_ID> <ENCLAVE_CONFIG_ID> <PUBLIC_IP> score_oracle SCORE_ORACLE
```

#### 5. Initialize Oracle
```bash
./initialize_oracle.sh <PACKAGE_ID>
```

#### 6. Update Score
```bash
./update_score.sh <PUBLIC_IP> <PACKAGE_ID> <ORACLE_ID> <ENCLAVE_ID> 0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba
```

## Usage Examples

### Query Score from Enclave
```bash
curl "http://<PUBLIC_IP>:3000/score?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba"
```

### Query Score from Blockchain
```bash
cd contracts/script
./get_score.sh <PACKAGE_ID> <ORACLE_ID>
```

## Data Schema

### On-Chain Storage

```move
public struct ScoreData has copy, drop, store {
    score: u64,              // Transaction count
    wallet_address: String,  // EVM address (0x...)
}

public struct ScoreOracle<phantom T> has key {
    id: UID,
    scores: Table<u64, ScoreData>,  // timestamp -> score data
    latest_score: u64,
    latest_wallet_address: String,
    latest_timestamp: u64,
}
```

### BCS Serialization

**Critical:** Field order MUST match between Move and JavaScript:

```move
// Move
public struct ScoreUpdatePayload has copy, drop {
    score: u64,              // First
    wallet_address: String,  // Second
}
```

```javascript
// JavaScript
const ScoreUpdatePayload = bcs.struct('ScoreUpdatePayload', {
  score: bcs.u64(),           // First
  wallet_address: bcs.string(), // Second
});
```

## Security

### Signature Verification

The oracle verifies that scores are signed by a registered enclave with correct PCR measurements:

1. Enclave signs `IntentMessage<ScoreUpdatePayload>` with secp256k1
2. Smart contract verifies signature matches registered enclave's public key
3. Score is stored only if signature is valid

### PCR Attestation

PCR values ensure the enclave is running authentic code:
- **PCR0**: Enclave image file hash
- **PCR1**: Enclave kernel hash
- **PCR2**: Enclave application hash
- **PCR16**: Application image hash

## Development

### Local Testing

```bash
# Install Node.js dependencies
cd app
npm install

# Test API endpoint
curl -s "https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba" | jq

# Build contracts
cd ../contracts
sui move build
```

### Project Structure

```
oracle/
├── contracts/
│   ├── sources/
│   │   ├── score_oracle.move  # Main oracle contract
│   │   └── enclave.move       # Attestation module
│   ├── script/
│   │   ├── initialize_oracle.sh
│   │   ├── update_score.sh
│   │   ├── get_score.sh
│   │   └── register_enclave.sh
│   └── Move.toml
├── app/
│   ├── src/
│   │   └── index.js           # Enclave application
│   ├── package.json
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── build.nix              # Reproducible build
├── flake.nix                  # Nix flake configuration
├── nix.sh                     # Build helper
├── deploy.sh                  # Automated deployment
└── deployment.env             # Generated deployment IDs
```

## Configuration

### Environment Variables

- `PRIVATE_KEY` - Sui wallet private key (required for deployment)
- `DOCKER_REGISTRY` - Docker Hub username or registry URL

### Deployment Artifacts

After deployment, `deployment.env` contains:
```bash
PACKAGE_ID=0x...
ENCLAVE_CONFIG_ID=0x...
CAP_ID=0x...
PUBLIC_IP=x.x.x.x
ENCLAVE_ID=0x...
ORACLE_ID=0x...
```

## Troubleshooting

### Contract Build Fails
- Verify Sui CLI version: `sui --version`
- Check Move.toml dependencies match framework version

### Enclave Deployment Fails
- Ensure Docker is running and logged in
- Check Oyster CVM CLI is installed: `oyster-cvm --version`
- Verify wallet has sufficient SUI for deployment

### Signature Verification Fails
- Confirm BCS field order matches between Move and JavaScript
- Check enclave public key matches registered key: `GET /public-key`
- Verify PCR values in smart contract match built image

### API Returns 503
- Check n8n webhook endpoint is accessible
- Verify address format: `0x` + 40 hex characters
- Look for timeout or network errors in enclave logs

## References

- [Oyster CVM Documentation](https://docs.marlin.org/oyster-cvm)
- [Sui Move Documentation](https://docs.sui.io/guides/developer/sui-101/move-overview)
- [Nautilus Framework](https://github.com/MystenLabs/nautilus)
