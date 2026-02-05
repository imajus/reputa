# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EVM Transaction Score Oracle - A Trusted Execution Environment (TEE) oracle that fetches EVM transaction counts from n8n webhook API, signs them inside a TEE enclave, and stores verified scores on the Sui blockchain.

**Data Flow:**
```
User Query → Enclave API → n8n Webhook → EVM Transaction Data
                ↓
         Calculate Score (tx count)
                ↓
         Sign with TEE secp256k1 Key
                ↓
    Sui Blockchain (signature verified by smart contract)
```

## Build Commands

### Smart Contracts (Move)
```bash
cd contracts
sui move build                    # Build contracts
sui move test                     # Run tests (if any)
sui client publish --gas-budget 100000000 --with-unpublished-dependencies
```

### Node.js Enclave
```bash
cd app
npm install                       # Install dependencies
node src/index.js /path/to/key   # Run locally (requires signing key)
```

### Reproducible Docker Build (Nix)
```bash
./nix.sh build-node-arm64        # For ARM64 (Apple Silicon, AWS Graviton)
./nix.sh build-node-amd64        # For AMD64 (x86_64)
```

### Full Deployment
```bash
export PRIVATE_KEY="your_sui_private_key"
export DOCKER_REGISTRY="your_dockerhub_username"
./deploy.sh                       # Automated deployment to Oyster CVM
```

After deployment, `deployment.env` contains all object IDs and IP addresses.

## Architecture

### Three-Component System

1. **Smart Contracts** (`contracts/sources/`)
   - `score_oracle.move` - Main oracle with signature verification
   - `enclave.move` - PCR attestation and enclave registration (from Nautilus framework)

2. **Node.js Enclave** (`app/src/index.js`)
   - HTTP server running inside TEE (Oyster CVM)
   - Endpoints: `/health`, `/public-key`, `/score?address=0x...`
   - Fetches data from: `https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address={ADDRESS}`

3. **Deployment Scripts** (`contracts/script/`)
   - `initialize_oracle.sh` - Create shared ScoreOracle object
   - `update_score.sh` - Fetch signed score from enclave and submit to blockchain
   - `get_score.sh` - Query latest score from blockchain state
   - `register_enclave.sh` - Register enclave with PCR attestation

### Critical: BCS Serialization

**Field order MUST be identical between Move and JavaScript:**

```move
// contracts/sources/score_oracle.move
public struct ScoreUpdatePayload has copy, drop {
    score: u64,              // First
    wallet_address: String,  // Second
}
```

```javascript
// app/src/index.js
const ScoreUpdatePayload = bcs.struct('ScoreUpdatePayload', {
  score: bcs.u64(),           // First - MUST match Move order
  wallet_address: bcs.string(), // Second - MUST match Move order
});
```

Any mismatch causes signature verification to fail on-chain.

### Signature Flow

1. **Enclave signs:** `SHA256(BCS(IntentMessage<ScoreUpdatePayload>))` with secp256k1
2. **Smart contract verifies:** Using `ecdsa_k1::secp256k1_verify(signature, enclave_pk, message_bytes, 1)`
3. **Hash flag = 1:** Tells Sui to hash with SHA256 before verification

### Entry Function Constraint

**Move entry functions cannot accept `String` parameters** - only primitives like `u64`, `vector<u8>`, `address`.

Solution in `score_oracle.move:199-217`:
```move
entry fun update_wallet_score(
    wallet_address: vector<u8>,  // Accept as bytes
    ...
) {
    let wallet_address_string = wallet_address.to_string();  // Convert inside
    update_score(..., wallet_address_string, ...);
}
```

The script `update_score.sh` converts the address string to byte vector using Python.

## Deployment Architecture

### PCR Attestation

PCR (Platform Configuration Register) values ensure the enclave runs authentic code:
- **PCR0**: Enclave image file hash
- **PCR1**: Enclave kernel hash
- **PCR2**: Enclave application hash
- **PCR16**: Application image hash

These are extracted from Oyster deployment and stored in the smart contract. Only enclaves with matching PCRs can register.

### Deployment Flow (deploy.sh)

1. Build and publish Move contracts → get PACKAGE_ID
2. Build Docker image with Nix (reproducible) → get image digest
3. Deploy to Oyster CVM → get PUBLIC_IP and PCR values
4. Update PCRs in EnclaveConfig on-chain
5. Register enclave with attestation document → get ENCLAVE_ID
6. Initialize oracle → get ORACLE_ID
7. Submit test score to verify end-to-end flow

All IDs saved to `deployment.env` for subsequent operations.

## Key Technical Details

### n8n API Response Format
```json
{
  "EVM": {
    "Events": [
      { "Block": {...}, "Log": {...}, "Transaction": {...} },
      ...
    ]
  }
}
```

Score = `EVM.Events.length` (transaction count).

### On-Chain Storage
```move
public struct ScoreOracle<phantom T> has key {
    scores: Table<u64, ScoreData>,  // timestamp → score data
    latest_score: u64,               // Cached latest
    latest_wallet_address: String,
    latest_timestamp: u64,
}
```

Historical scores stored by timestamp; latest values cached for cheap queries.

### Nix Build Configuration

`app/build.nix` uses `buildNpmPackage` with locked dependencies:
- `npmDepsHash` must match `package-lock.json` for reproducible builds
- If you change dependencies, Nix will fail with hash mismatch - update hash in error message

`flake.nix` builds for both amd64 and arm64 architectures using cross-compilation when needed.

## Testing

### Local Testing (without TEE)
```bash
# Test n8n API
curl "https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba"

# Build contracts
cd contracts && sui move build

# Install Node.js deps
cd app && npm install
```

### Query Deployed System
```bash
source deployment.env

# Query enclave directly
curl "http://${PUBLIC_IP}:3000/score?address=0x..."

# Query blockchain state
./contracts/script/get_score.sh $PACKAGE_ID $ORACLE_ID

# Submit new score
./contracts/script/update_score.sh $PUBLIC_IP $PACKAGE_ID $ORACLE_ID $ENCLAVE_ID 0x...
```

## Common Issues

### Signature Verification Fails
- Check BCS field order matches between Move and JavaScript
- Verify enclave public key matches: `curl http://$PUBLIC_IP:3000/public-key`
- Confirm PCR values in contract match deployed image

### Nix Build Hash Mismatch
- Update `npmDepsHash` in `app/build.nix` with the hash from error message
- Occurs when `package-lock.json` changes

### VMVerificationOrDeserializationError
- Entry function parameter type issue
- Ensure `String` parameters are passed as `vector<u8>` and converted inside
- Check `update_score.sh` converts address to byte array with Python

## External Dependencies

- **Sui Framework**: testnet branch for Move contracts
- **Oyster CVM**: TEE deployment platform (AWS Nitro Enclaves)
- **Nautilus Framework**: Enclave attestation pattern (enclave.move)
- **n8n Webhook**: EVM transaction data source
