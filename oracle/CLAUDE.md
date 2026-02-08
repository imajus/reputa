# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EVM Transaction Score Oracle - A Trusted Execution Environment (TEE) oracle that analyzes EVM wallet activity and questionnaire responses using AI, signs reputation scores inside a TEE enclave, and stores verified scores on the Sui blockchain.

**Data Flow:**
```
Frontend → POST /score (address + questionnaire) → Enclave API
                                                        ↓
                           POST https://reputa-data.majus.app/aggregate
                           Body: { wallet_address: "0x..." }
                           (aggregated EVM analytics across protocols)
                                                        ↓
                            extractWalletFeatures() + formatQuestionnaireForAI()
                                                        ↓
                            Ollama AI Scoring (5-dimension breakdown)
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
   - Endpoints:
     - `GET /health` - Health check with Ollama status
     - `GET /public-key` - Get enclave's secp256k1 public key
     - `GET /score?address=0x...` - Get score without questionnaire (backward compatible)
     - `POST /score` - Get score with optional questionnaire data
   - Fetches data from: `POST https://reputa-data.majus.app/aggregate` with `{ wallet_address: "0x..." }`
   - AI scoring via Ollama (llama3.2:1b model)

3. **Deployment Scripts** (`contracts/script/`)
   - `initialize_oracle.sh` - Create shared ScoreRegistry object
   - `update_score.sh` - Fetch signed score from enclave and submit to blockchain
   - `get_score.sh` - Query owned WalletScore objects from blockchain
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
6. Initialize registry → get REGISTRY_ID
7. Submit test score to verify end-to-end flow

All IDs saved to `deployment.env` for subsequent operations.

## Key Technical Details

### Aggregate API Response Format

The aggregate API (`POST https://reputa-data.majus.app/aggregate`) returns rich analytical data with pre-calculated metrics:

```json
{
  "wallet": "0x...",
  "wallet_metadata": {
    "wallet_age_days": 1262,
    "total_transactions": 2681,
    "unique_counterparties": 315,
    "average_txs_per_month": 63.73
  },
  "defi_analysis": {
    "protocol_interactions": {
      "curve": true,
      "morpho": true,
      "total_protocols": 2
    }
  },
  "lending_history": {
    "protocol_analysis": {
      "protocols": {
        "0x...": {
          "borrow_count": 5,
          "repay_count": 5,
          "liquidate_count": 0
        }
      }
    }
  },
  "tokens": {
    "concentration": {
      "diversification_score": 45,
      "herfindahl_index": 0.8,
      "num_tokens": 49
    }
  },
  "nfts": {
    "poaps": [...],
    "legit_nfts": [...]
  },
  "eth_balance": 0.082
}
```

The oracle uses `extractWalletFeatures()` to parse this data and pass it to AI scoring.

### AI Scoring with Questionnaire Integration

The oracle accepts optional questionnaire responses via POST /score:

```json
{
  "address": "0x...",
  "questionnaire": [
    {"question": "Who controls this wallet?", "answer": "individual"},
    {"question": "What is the loan for?", "answer": "working capital"}
  ]
}
```

The AI scoring function analyzes both on-chain activity and questionnaire responses to generate:
- **Total Score** (0-1000): Overall reputation score
- **Score Breakdown** (5 dimensions, each 0-100):
  - `activity`: Transaction count, frequency, recent engagement
  - `maturity`: Account age, usage consistency
  - `diversity`: Protocol count, token diversification, unique counterparties
  - `riskBehavior`: Liquidations, borrow/repay ratio, liability disclosure
  - `surveyMatch`: Coherence between stated intent and on-chain behavior (50 if no questionnaire)

Response format:
```json
{
  "score": 750,
  "wallet_address": "0x...",
  "timestamp_ms": 1738742400000,
  "signature": "0x...",
  "metadata": {
    "scoreBreakdown": {
      "activity": 85,
      "maturity": 78,
      "diversity": 62,
      "riskBehavior": 88,
      "surveyMatch": 72
    },
    "reasoning": "Account shows strong engagement...",
    "risk_factors": ["High token concentration"],
    "strengths": ["Consistent repayment history"],
    "features": { ... }
  }
}
```

**Note:** Only the `score`, `wallet_address`, and `timestamp_ms` are signed and stored on-chain. The `metadata` (including scoreBreakdown) is unsigned and returned for frontend display only.

### JSON Schema Validation with Retry Logic

The oracle implements robust validation to ensure AI responses meet quality standards:

**Validation Pipeline:**
1. **Schema Validation**: Uses ajv library to verify response structure, field types, and value ranges
2. **Cross-Validation**: Verifies total score matches weighted breakdown formula within 2% tolerance
3. **Retry with Temperature Decay**: On validation failure, retries up to 3 times with decreasing temperature (0.3 → 0.2 → 0.1)
4. **Fallback**: If all retries fail, falls back to simple transaction-based scoring

**Schema Structure:**
```javascript
const responseSchema = {
  type: 'object',
  properties: {
    score: { type: 'integer', minimum: 0, maximum: 1000 },
    scoreBreakdown: {
      type: 'object',
      properties: {
        activity: { type: 'integer', minimum: 0, maximum: 100 },
        maturity: { type: 'integer', minimum: 0, maximum: 100 },
        diversity: { type: 'integer', minimum: 0, maximum: 100 },
        riskBehavior: { type: 'integer', minimum: 0, maximum: 100 },
        surveyMatch: { type: 'integer', minimum: 0, maximum: 100 }
      },
      required: ['activity', 'maturity', 'diversity', 'riskBehavior', 'surveyMatch']
    },
    reasoning: { type: 'string', minLength: 10, maxLength: 500 },
    risk_factors: { type: 'array', items: { type: 'string' } },
    strengths: { type: 'array', items: { type: 'string' } }
  },
  required: ['score', 'scoreBreakdown', 'reasoning', 'risk_factors', 'strengths']
};
```

**Cross-Validation Formula:**
```javascript
calculatedScore = (activity × 2.0) + (maturity × 2.0) + (diversity × 2.0) + (riskBehavior × 2.5) + (surveyMatch × 1.5)
tolerance = max(2, calculatedScore × 0.02)
valid = |score - calculatedScore| <= tolerance
```

**Logging:**
- Each retry attempt is logged with temperature value
- Validation failures include detailed error messages and field details
- Successful attempts log which retry succeeded

**Performance:**
- Schema validation overhead: ~100-200ms per request
- Retry overhead: ~3-8s per retry (rarely triggered)
- Expected retry rate: <5% of requests
- Target metrics: >95% schema compliance, <1% fallback rate

### Deterministic Seeding for Reproducibility

The oracle uses deterministic seeding based on wallet addresses to improve score consistency:

**Seed Generation:**
```javascript
function generateSeedFromAddress(address) {
  const normalized = address.toLowerCase().replace(/^0x/, '');
  const hash = createHash('sha256').update(normalized).digest();
  return hash.readUInt32BE(0);
}
```

**Ollama Configuration:**
- Temperature: 0.1 (reduced from 0.3 for better determinism)
- Seed: SHA-256 hash of normalized wallet address (first 4 bytes as u32)

**Characteristics:**
- Same wallet always gets the same seed
- Different wallets get different seeds (SHA-256 prevents collisions)
- Improves reproducibility when scoring the same wallet multiple times
- First-run inconsistencies still possible due to Ollama/LLM platform quirks
- Subsequent runs for same wallet are highly consistent (>90% reproducibility target)

**Limitations:**
- Not 100% deterministic due to floating-point precision and GPU non-determinism
- Temperature 0.1 balances determinism with quality (0.0 can degrade reasoning)
- Seed changes score distribution across wallets but maintains fairness

**Logging:** Seed value is logged in debug output for each scoring request.

### On-Chain Storage
```move
// User-owned score object (created per wallet per user)
public struct WalletScore has key, store {
    id: UID,
    score: u64,
    wallet_address: String,  // EVM address
    timestamp_ms: u64,
    version: u64,
}

// Shared registry for wallet → score_object_id lookups
public struct ScoreRegistry<phantom T> has key {
    id: UID,
    // Dynamic fields: wallet_address (String) → ID (object ID)
}
```

Each user owns their WalletScore object(s). Registry provides efficient lookup by EVM wallet address. Updates create new versions.

### Nix Build Configuration

`app/build.nix` uses `buildNpmPackage` with locked dependencies:
- `npmDepsHash` must match `package-lock.json` for reproducible builds
- If you change dependencies, Nix will fail with hash mismatch - update hash in error message

`flake.nix` builds for both amd64 and arm64 architectures using cross-compilation when needed.

## Testing

### Local Testing (without TEE)
```bash
# Test aggregation API
curl -X POST https://reputa-data.majus.app/aggregate \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba"}'

# Build contracts
cd contracts && sui move build

# Install Node.js deps
cd app && npm install
```

### Query Deployed System
```bash
source deployment.env

# Query enclave directly
curl "http://${PUBLIC_IP}:8880/score?address=0x..."

# Query blockchain state
./contracts/script/get_score.sh $PACKAGE_ID $REGISTRY_ID

# Submit new score
./contracts/script/update_score.sh $PUBLIC_IP $PACKAGE_ID $REGISTRY_ID $ENCLAVE_ID 0x...
```

## Common Issues

### Signature Verification Fails
- Check BCS field order matches between Move and JavaScript
- Verify enclave public key matches: `curl http://$PUBLIC_IP:8880/public-key`
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
- **Reputa Data API** (`https://reputa-data.majus.app/aggregate`): Aggregated EVM transaction analytics

## References

- In-depth Marlin Oyster plarform guide: @../docs/oyster.md
- Detailed breakdown of scoring framework: @../docs/scoring.md