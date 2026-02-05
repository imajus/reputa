# Building Marlin Oyster Applications for Sui Nautilus: Complete Guide (Node.js)

A comprehensive guide to building Trusted Execution Environment (TEE) applications using Marlin Oyster enclaves and Sui blockchain, demonstrated through a decentralized price oracle.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Smart Contract Development](#smart-contract-development)
5. [Enclave Application Development](#enclave-application-development)
6. [Reproducible Builds](#reproducible-builds)
7. [Deployment](#deployment)
8. [Verification](#verification)
9. [Testing](#testing)
10. [Constraints and Best Practices](#constraints-and-best-practices)
11. [Advanced Topics](#advanced-topics)
    - [Key Management Strategies](#key-management-strategies)
    - [Multi-Enclave Support](#multi-enclave-support)
    - [Custom Data Types](#custom-data-types)
12. [Troubleshooting](#troubleshooting)
13. [Resources](#resources)

---

## Overview

This guide demonstrates how to build a decentralized application that combines:
- **Sui Move Smart Contracts**: On-chain data storage and cryptographic verification
- **AWS Nitro Enclaves** (via Oyster): Hardware-isolated execution environment
- **secp256k1 Signatures**: Cryptographic proof of data authenticity
- **PCR Attestation**: Verifiable proof of enclave code integrity

**Example Application**: A price oracle that fetches SUI token prices from CoinGecko, signs them cryptographically inside a TEE, and stores them on Sui blockchain with verifiable attestation.

### Why Use TEEs with Blockchain?

- **Hardware Isolation**: Enclave code runs in isolated memory with encryption
- **Verifiable Execution**: PCR values prove exact code running in enclave
- **Private Key Security**: Signing keys never leave the enclave
- **Trust Minimization**: Users can verify enclave code matches source

---

## Architecture

### System Overview

```
┌─────────────────┐
│   External API  │  (e.g., CoinGecko)
│   (Data Source) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐      ┌──────────────────────┐
│   Oyster Enclave (AWS Nitro)    │      │   Sui Blockchain     │
│  ┌───────────────────────────┐  │      │  ┌────────────────┐  │
│  │  Node.js HTTP Server      │  │      │  │  Move Contract │  │
│  │  - Fetch data from API    │  │      │  │  - Verify sigs │  │
│  │  - Sign with secp256k1    │  │──────┼─▶│  - Store data  │  │
│  │  - Return signed payload  │  │      │  │  - Check PCRs  │  │
│  └───────────────────────────┘  │      │  └────────────────┘  │
│  ┌───────────────────────────┐  │      │         │            │
│  │  Private Key (32 bytes)   │  │      │         ▼            │
│  │  - Generated in enclave   │  │      │  ┌────────────────┐  │
│  │  - Never leaves TEE       │  │      │  │ Historical Data│  │
│  └───────────────────────────┘  │      │  │  (Table<u64>)  │  │
│                                  │      │  └────────────────┘  │
│  PCR0, PCR1, PCR2, PCR16        │      │                      │
│  (Attestation Values)            │      │                      │
└─────────────────────────────────┘      └──────────────────────┘
```

### Data Flow

1. **Enclave Initialization**
   - Oyster CVM deploys Docker container to AWS Nitro Enclave
   - Enclave generates secp256k1 private key (or loads from volume)
   - PCR values computed from enclave image

2. **Registration Phase**
   - Fetch attestation document from enclave
   - Extract PCR0, PCR1, PCR2, PCR16 values
   - Call Move contract to register enclave with PCRs
   - Store enclave public key on-chain

3. **Data Update Flow**
   - Anyone calls enclave HTTP endpoint to fetch signed data
   - Enclave fetches data from external API
   - Enclave signs data with BCS serialization + secp256k1
   - Caller submits signed data to blockchain
   - Move contract verifies signature against registered enclave
   - Data stored on-chain with timestamp

4. **Verification**
   - Users rebuild enclave from source
   - Compare PCR values with on-chain registration
   - Cryptographic proof that deployed enclave matches source code

---

## Prerequisites

### Required Tools

1. **Sui CLI** (v1.35+)
   ```bash
   curl -sSL https://docs.sui.io/install.sh | bash
   ```

2. **Docker** (v29+ recommended)
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com | sh

   # Docker 29+ ensures stable digests after `docker load`
   docker --version
   ```

3. **Oyster CVM CLI**
   ```bash
   # Install from Marlin repository
   curl -sSL https://docs.marlin.org/oyster/install.sh | bash
   ```

4. **Nix Package Manager** (for reproducible builds)
   ```bash
   curl -L https://nixos.org/nix/install | sh
   # Enable flakes
   mkdir -p ~/.config/nix
   echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
   ```

5. **Node.js** (v20+, for local development)
   ```bash
   # Using nvm
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
   nvm install 20
   ```

### Wallet Setup

1. **Create Sui Wallet**
   ```bash
   sui client new-address ed25519
   sui client switch --address <ADDRESS>
   ```

2. **Fund Wallet**
   - SUI tokens for gas fees
   - USDC for Oyster enclave deployment costs
   - Get testnet tokens: https://docs.sui.io/guides/developer/getting-started/get-coins

3. **Export Private Key**
   ```bash
   export PRIVATE_KEY="suiprivkey..."  # Your wallet private key
   ```

---

## Smart Contract Development

### Project Structure

```
contracts/
├── sources/
│   ├── oyster_demo.move      # Main application logic (price oracle)
│   └── enclave.move          # Enclave registration & attestation
├── script/
│   ├── initialize_oracle.sh  # Create oracle object
│   ├── register_enclave.sh   # Register enclave on-chain
│   ├── update_price.sh       # Submit signed data
│   └── get_price.sh          # Query oracle
├── Move.toml                 # Package configuration
└── README.md
```

### Move.toml Configuration

```toml
[package]
name = "oyster_demo"
edition = "2024.beta"

[dependencies]
Sui = { git = "https://github.com/MystenLabs/sui.git", subdir = "crates/sui-framework/packages/sui-framework", rev = "framework/testnet" }
NitroAttestation = { git = "https://github.com/MystenLabs/sui.git", subdir = "crates/sui-framework/packages/sui-nitro-attestation", rev = "framework/testnet" }

[dependencies.enclave]
published-at = "0x..."  # Update after first publish
source = { local = "../../nautilus/move/enclave" }

[addresses]
oyster_demo = "0x0"
enclave = "0x0"
```

### Enclave Registration Contract (enclave.move)

The enclave registration system provides attestation verification:

```move
module enclave::enclave;

use std::bcs;
use std::string::String;
use sui::ecdsa_k1;
use sui::nitro_attestation::NitroAttestationDocument;

// PCR tuple: (PCR0, PCR1, PCR2, PCR16)
public struct Pcrs(vector<u8>, vector<u8>, vector<u8>, vector<u8>) has copy, drop, store;

// Expected PCR configuration for this application
public struct EnclaveConfig<phantom T> has key {
    id: UID,
    name: String,
    pcrs: Pcrs,
    capability_id: ID,
    version: u64,  // Incremented when PCRs change
}

// A verified enclave instance with its secp256k1 public key
public struct Enclave<phantom T> has key {
    id: UID,
    pk: vector<u8>,           // Compressed secp256k1 public key (33 bytes)
    config_version: u64,      // Must match EnclaveConfig version
    owner: address,
}

// Capability to update enclave configuration
public struct Cap<phantom T> has key, store {
    id: UID,
}

// Create new capability using one-time witness
public fun new_cap<T: drop>(_: T, ctx: &mut TxContext): Cap<T> {
    Cap { id: object::new(ctx) }
}

// Create enclave configuration with initial PCR values
public fun create_enclave_config<T: drop>(
    cap: &Cap<T>,
    name: String,
    pcr0: vector<u8>,   // Enclave image file hash
    pcr1: vector<u8>,   // Enclave kernel hash
    pcr2: vector<u8>,   // Enclave application hash
    pcr16: vector<u8>,  // Application image hash
    ctx: &mut TxContext,
) {
    let enclave_config = EnclaveConfig<T> {
        id: object::new(ctx),
        name,
        pcrs: Pcrs(pcr0, pcr1, pcr2, pcr16),
        capability_id: cap.id.to_inner(),
        version: 0,
    };
    transfer::share_object(enclave_config);
}

// Register a new enclave instance with attestation document
public fun register_enclave<T>(
    enclave_config: &EnclaveConfig<T>,
    document: NitroAttestationDocument,
    ctx: &mut TxContext,
) {
    // Extract and verify public key from attestation
    let pk = enclave_config.load_pk(&document);

    let enclave = Enclave<T> {
        id: object::new(ctx),
        pk,
        config_version: enclave_config.version,
        owner: ctx.sender(),
    };
    transfer::share_object(enclave);
}

// Update PCRs when enclave code changes
public fun update_pcrs<T: drop>(
    config: &mut EnclaveConfig<T>,
    cap: &Cap<T>,
    pcr0: vector<u8>,
    pcr1: vector<u8>,
    pcr2: vector<u8>,
    pcr16: vector<u8>,
) {
    cap.assert_is_valid_for_config(config);
    config.pcrs = Pcrs(pcr0, pcr1, pcr2, pcr16);
    config.version = config.version + 1;  // Increment version
}

// Verify signature from enclave
public fun verify_signature<T, P: drop>(
    enclave: &Enclave<T>,
    intent_scope: u8,
    timestamp_ms: u64,
    payload: P,
    signature: &vector<u8>,
): bool {
    let intent_message = create_intent_message(intent_scope, timestamp_ms, payload);
    let payload = bcs::to_bytes(&intent_message);
    ecdsa_k1::secp256k1_verify(signature, &enclave.pk, &payload, 1)  // SHA256
}

// Helper: Load and verify public key from attestation
fun load_pk<T>(enclave_config: &EnclaveConfig<T>, document: &NitroAttestationDocument): vector<u8> {
    // Verify PCRs match expected values
    assert!(document.to_pcrs() == enclave_config.pcrs, EInvalidPCRs);

    // Extract public key from attestation
    let mut pk = (*document.public_key()).destroy_some();

    // Convert to compressed format if needed (33 bytes)
    if (pk.length() == 64) {
        pk = compress_secp256k1_pubkey(&pk);
    };

    assert!(pk.length() == 33, EInvalidPublicKeyLength);
    pk
}

// Helper: Compress secp256k1 public key from 64 to 33 bytes
fun compress_secp256k1_pubkey(uncompressed: &vector<u8>): vector<u8> {
    let mut compressed = vector::empty<u8>();
    let y_last_byte = uncompressed[63];
    let prefix = if (y_last_byte % 2 == 0) { 0x02 } else { 0x03 };
    compressed.push_back(prefix);
    let mut i = 0;
    while (i < 32) {
        compressed.push_back(uncompressed[i]);
        i = i + 1;
    };
    compressed
}
```

**Key Concepts**:
- **PCR Values**: Hardware-measured hashes of enclave code
- **Attestation Document**: Cryptographic proof from AWS Nitro
- **Public Key Storage**: Compressed secp256k1 format (33 bytes)
- **Versioning**: Config version increments when PCRs change

### Application Contract (oyster_demo.move)

The price oracle implementation with signature verification:

```move
module oyster_demo::oyster_demo;

use std::bcs;
use sui::table::{Self, Table};
use sui::event;
use sui::ecdsa_k1;
use enclave::enclave::{Self, Enclave};

// Error codes
const EInvalidSignature: u64 = 0;
const ENoPriceAtTimestamp: u64 = 1;
const ENoPriceAvailable: u64 = 2;

// One-time witness for module initialization
public struct OYSTER_DEMO has drop {}

// IntentMessage wrapper - must match enclave serialization
public struct IntentMessage<T: copy + drop> has copy, drop {
    intent: u8,
    timestamp_ms: u64,
    data: T,
}

// Main oracle storage
public struct PriceOracle<phantom T> has key {
    id: UID,
    prices: Table<u64, u64>,     // timestamp -> price mapping
    latest_price: u64,
    latest_timestamp: u64,
}

// Signed payload structure
public struct PriceUpdatePayload has copy, drop {
    price: u64,  // Price in micro-units (6 decimals)
}

// Events
public struct PriceUpdated has copy, drop {
    price: u64,
    timestamp: u64,
}

public struct OracleCreated has copy, drop {
    oracle_id: ID,
}

// Create oracle (internal)
fun create_oracle<T>(ctx: &mut TxContext): PriceOracle<T> {
    let oracle = PriceOracle<T> {
        id: object::new(ctx),
        prices: table::new(ctx),
        latest_price: 0,
        latest_timestamp: 0,
    };
    event::emit(OracleCreated { oracle_id: object::id(&oracle) });
    oracle
}

// Update price with signature verification
fun update_price<T: drop>(
    oracle: &mut PriceOracle<T>,
    enclave: &Enclave<T>,
    price: u64,
    timestamp_ms: u64,
    signature: vector<u8>,
) {
    // Create payload that was signed
    let payload = PriceUpdatePayload { price };

    // Wrap in IntentMessage
    let intent_message = IntentMessage {
        intent: 0u8,
        timestamp_ms,
        data: payload,
    };

    // BCS serialize for signature verification
    let message_bytes = bcs::to_bytes(&intent_message);
    let enclave_pk = enclave.pk();

    // Verify secp256k1 signature with SHA256 hash
    let is_valid = ecdsa_k1::secp256k1_verify(
        &signature,
        enclave_pk,
        &message_bytes,
        1  // SHA256 hash function flag
    );

    assert!(is_valid, EInvalidSignature);

    // Store price
    table::add(&mut oracle.prices, timestamp_ms, price);

    // Update latest if newer
    if (timestamp_ms > oracle.latest_timestamp) {
        oracle.latest_price = price;
        oracle.latest_timestamp = timestamp_ms;
    };

    event::emit(PriceUpdated { price, timestamp: timestamp_ms });
}

// Public getter: latest price
public fun get_latest_price<T>(oracle: &PriceOracle<T>): (u64, u64) {
    assert!(oracle.latest_timestamp > 0, ENoPriceAvailable);
    (oracle.latest_price, oracle.latest_timestamp)
}

// Public getter: historical price
public fun get_price_at_timestamp<T>(oracle: &PriceOracle<T>, timestamp: u64): u64 {
    assert!(table::contains(&oracle.prices, timestamp), ENoPriceAtTimestamp);
    *table::borrow(&oracle.prices, timestamp)
}

// Module initializer - called once at publish
fun init(witness: OYSTER_DEMO, ctx: &mut TxContext) {
    // Create capability for enclave config updates
    let cap = enclave::new_cap(witness, ctx);

    // Create enclave configuration with placeholder PCRs
    cap.create_enclave_config(
        b"SUI Price Oracle Enclave".to_string(),
        x"00...",  // PCR0 - update after building enclave
        x"00...",  // PCR1 - update after building enclave
        x"00...",  // PCR2 - update after building enclave
        x"00...",  // PCR16 - update after building enclave
        ctx,
    );

    // Transfer capability to deployer
    transfer::public_transfer(cap, ctx.sender());
}

// Entry function: create and share oracle
entry fun initialize_oracle(ctx: &mut TxContext) {
    let oracle = create_oracle<OYSTER_DEMO>(ctx);
    transfer::share_object(oracle);
}

// Entry function: update price (callable by anyone with valid signature)
entry fun update_sui_price(
    oracle: &mut PriceOracle<OYSTER_DEMO>,
    enclave: &Enclave<OYSTER_DEMO>,
    price: u64,
    timestamp_ms: u64,
    signature: vector<u8>,
) {
    update_price(oracle, enclave, price, timestamp_ms, signature);
}
```

**Key Features**:
- **Permissionless Updates**: Anyone can submit signed data
- **Historical Storage**: Table mapping timestamps to values
- **Event Emissions**: Track all price updates on-chain
- **Signature Verification**: Only accepts data from registered enclaves

### Deploy Smart Contracts

```bash
cd contracts

# Build contracts
sui move build

# Publish to blockchain
sui client publish --gas-budget 100000000 --with-unpublished-dependencies

# Extract object IDs from output:
# - PACKAGE_ID: Published package
# - ENCLAVE_CONFIG_ID: Shared EnclaveConfig object
# - CAP_ID: Owned Cap object for PCR updates
```

---

## Enclave Application Development

### Project Structure

```
enclave_node/
├── src/
│   └── index.js              # Express.js HTTP server
├── package.json              # Dependencies (pure JS only)
├── package-lock.json         # Locked dependency versions
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Oyster deployment config
└── build.nix                 # Nix build configuration
```

### Dependencies (package.json)

```json
{
  "name": "sui-price-oracle-node",
  "version": "0.1.0",
  "type": "module",
  "dependencies": {
    "@mysten/bcs": "^1.9.2",        // BCS serialization for Move compatibility
    "@noble/secp256k1": "^3.0.0",   // Pure JS secp256k1 (no native modules)
    "@noble/hashes": "^2.0.1",      // SHA256 hashing
    "axios": "^1.13.2",             // HTTP client for API calls
    "express": "^5.2.1"             // HTTP server framework
  }
}
```

**Critical**: Use pure JavaScript libraries (no native modules) for reproducible builds across architectures.

### Enclave Server Implementation (src/index.js)

```javascript
import express from 'express';
import axios from 'axios';
import { sign, getPublicKey, hashes } from '@noble/secp256k1';
import { sha256 } from '@noble/hashes/sha2.js';
import { hmac } from '@noble/hashes/hmac.js';
import { createHash } from 'crypto';
import fs from 'fs';
import { bcs } from '@mysten/bcs';

// Configure @noble/secp256k1 to use @noble/hashes
hashes.sha256 = sha256;
hashes.hmacSha256 = (key, msg) => hmac(sha256, key, msg);

// Define BCS structures matching Move contract
const PriceUpdatePayload = bcs.struct('PriceUpdatePayload', {
  price: bcs.u64(),
});

function IntentMessage(DataType) {
  return bcs.struct('IntentMessage', {
    intent: bcs.u8(),
    timestamp_ms: bcs.u64(),
    data: DataType,
  });
}

const IntentMessagePriceUpdate = IntentMessage(PriceUpdatePayload);
const INTENT_SCOPE = 0;

let signingKey = null;
const httpClient = axios.create();

// Fetch SUI price from CoinGecko
async function fetchSuiPrice() {
  const url = 'https://api.coingecko.com/api/v3/simple/price?ids=sui&vs_currencies=usd';
  try {
    const response = await httpClient.get(url, {
      headers: { 'User-Agent': 'SUI-Price-Oracle/1.0' }
    });
    return response.data.sui.usd;
  } catch (error) {
    console.error('Failed to fetch SUI price:', error.message);
    throw error;
  }
}

// Sign price data with secp256k1
function signPriceData(privateKey, price, timestampMs) {
  // Create payload matching Move struct
  const payload = { price };
  const intentMessage = {
    intent: INTENT_SCOPE,
    timestamp_ms: timestampMs,
    data: payload,
  };

  // BCS serialize
  const messageBytes = IntentMessagePriceUpdate.serialize(intentMessage).toBytes();

  // Hash with SHA256
  const hash = createHash('sha256').update(messageBytes).digest();

  // Sign with secp256k1
  const signature = sign(hash, privateKey, { prehash: false });

  // Return hex-encoded compact signature (64 bytes: r + s)
  return Buffer.from(signature).toString('hex');
}

// Load secp256k1 signing key from file
function loadSigningKeyFromFile(path) {
  const keyBytes = fs.readFileSync(path);
  if (keyBytes.length !== 32) {
    throw new Error(`Expected 32-byte secp256k1 private key, got ${keyBytes.length} bytes`);
  }
  try {
    getPublicKey(keyBytes);  // Validate key
  } catch (error) {
    throw new Error('Invalid secp256k1 private key');
  }
  return keyBytes;
}

// Express app
const app = express();

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Get public key endpoint
app.get('/public-key', (req, res) => {
  const publicKey = getPublicKey(signingKey, true);  // compressed
  res.json({ public_key: Buffer.from(publicKey).toString('hex') });
});

// Get signed price endpoint
app.get('/price', async (req, res) => {
  try {
    const priceUsd = await fetchSuiPrice();
    const price = Math.floor(priceUsd * 1_000_000);  // Convert to u64 (6 decimals)
    const timestampMs = Date.now();

    console.log(`Fetched SUI price: $${priceUsd.toFixed(6)} (raw: ${price})`);

    const signature = signPriceData(signingKey, price, timestampMs);

    res.json({ price, timestamp_ms: timestampMs, signature });
  } catch (error) {
    console.error('Failed to process price request:', error);
    res.status(503).json({ error: 'Failed to fetch or sign price' });
  }
});

// Main function
async function main() {
  const args = process.argv.slice(2);
  if (args.length !== 1) {
    console.error('Usage: node src/index.js <path-to-signing-key>');
    process.exit(1);
  }
  const keyPath = args[0];

  console.log(`Loading secp256k1 signing key from: ${keyPath}`);
  signingKey = loadSigningKeyFromFile(keyPath);
  console.log('Signing key loaded successfully');

  const publicKey = getPublicKey(signingKey, true);
  console.log(`Public key (hex): ${Buffer.from(publicKey).toString('hex')}`);

  const port = 3000;
  const host = '0.0.0.0';
  app.listen(port, host, () => {
    console.log(`Starting server on ${host}:${port}`);
  });
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
```

**Critical Points**:
1. **BCS Serialization**: Must exactly match Move struct layout
2. **IntentMessage Wrapper**: Prevents signature reuse across contexts
3. **Signature Format**: 64-byte compact format (r + s, no DER encoding)
4. **SHA256 Hashing**: Matches Move contract's `ecdsa_k1::secp256k1_verify` with flag=1
5. **Precision**: 6 decimal places (price × 10^6) for u64 compatibility

**Key Management Note**:
This implementation uses **ephemeral keys** from `/app/ecdsa.sec`, which are automatically generated by Oyster on enclave startup. Keys change with every deployment. For production applications requiring persistent keys across restarts or upgrades, see [Key Management Strategies](#key-management-strategies) in the Advanced Topics section.

### API Endpoints

#### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "ok"
}
```

#### GET /public-key
Returns enclave's compressed secp256k1 public key.

**Response**:
```json
{
  "public_key": "02a1b2c3..."  // 33 bytes hex (compressed)
}
```

#### GET /price
Fetches current SUI price, signs it, and returns signed payload.

**Response**:
```json
{
  "price": 2150000,                    // $2.15 in micro-units
  "timestamp_ms": 1738742400000,
  "signature": "a1b2c3d4..."           // 64 bytes hex (compact)
}
```

---

## Reproducible Builds

Reproducible builds ensure that anyone can rebuild your enclave and verify it matches the deployed version through PCR attestation.

### Why Reproducible Builds Matter

- **Verifiability**: Users can prove deployed code matches source
- **Security**: Prevents backdoors or malicious modifications
- **Trust**: PCR values provide cryptographic proof of code integrity

### Dockerfile (Multi-stage Build)

```dockerfile
# Build stage
FROM node:24-alpine AS builder

RUN apk add --no-cache python3 make g++

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Runtime stage
FROM node:24-alpine

WORKDIR /app/demo
COPY --from=builder /app/node_modules ./node_modules
COPY src ./src
COPY package*.json ./

ENTRYPOINT ["node", "src/index.js"]
CMD ["/app/ecdsa.sec"]
```

**Key Features**:
- Multi-stage build reduces image size
- Alpine Linux for minimal footprint
- `npm ci` for reproducible dependency installation
- No development dependencies in final image

### Nix Build Configuration (build.nix)

```nix
{ pkgs, version, arch ? "amd64" }:

let
  nodejs = pkgs.nodejs_20;

  # Filter source to only needed files
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        baseName = baseNameOf path;
        parentDir = baseNameOf (dirOf path);
      in
        baseName == "package.json" ||
        baseName == "package-lock.json" ||
        baseName == "src" ||
        parentDir == "src";
  };

  # Build Node.js application with locked dependencies
  app = pkgs.buildNpmPackage {
    pname = "sui-price-oracle-node";
    inherit version src nodejs;

    # Hash for dependencies - update when package-lock.json changes
    npmDepsHash = "sha256-HOZO9+yHJoSu3k653D8PKR/MJnML0jnpuMDnkrzdv9I=";

    dontNpmBuild = true;
    npmInstallFlags = [ "--omit=dev" ];

    installPhase = ''
      runHook preInstall
      mkdir -p $out/app
      cp -r . $out/app
      runHook postInstall
    '';
  };

in rec {
  inherit app nodejs;

  docker = pkgs.dockerTools.buildImage {
    name = "sui-price-oracle";
    tag = "node-reproducible-${arch}";
    copyToRoot = pkgs.buildEnv {
      name = "image-root";
      paths = [ nodejs app pkgs.cacert ];
      pathsToLink = [ "/bin" "/app" ];
    };
    config = {
      WorkingDir = "/app";
      Entrypoint = [ "${nodejs}/bin/node" "/app/src/index.js" "/app/ecdsa.sec" ];
      Env = [ "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt" ];
    };
  };

  default = docker;
}
```

**Key Features**:
- Deterministic builds with Nix
- Source filtering for clean builds
- npmDepsHash ensures exact dependencies
- CA certificates for HTTPS requests

### Root Flake Configuration (flake.nix)

```nix
{
  description = "SUI Price Oracle with Oyster Enclaves";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/release-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      version = "0.1.0";

      # Helper to build for specific architecture
      buildForArch = arch: system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
          import ./enclave_node/build.nix { inherit pkgs version arch; };
    in
    {
      packages = {
        # AMD64 (x86_64)
        x86_64-linux = {
          node-amd64 = buildForArch "amd64" "x86_64-linux";
        };

        # ARM64 (aarch64)
        aarch64-linux = {
          node-arm64 = buildForArch "arm64" "aarch64-linux";
        };
      };
    };
}
```

### Building Images

```bash
# Build for ARM64 (Apple Silicon, AWS Graviton)
./nix.sh build-node-arm64

# Build for AMD64 (Intel/AMD x86_64)
./nix.sh build-node-amd64

# Load into Docker
docker load < ./node-arm64-image.tar.gz

# Verify image digest
docker images --digests | grep sui-price-oracle
```

**Output**: `node-arm64-image.tar.gz` or `node-amd64-image.tar.gz`

### Updating npmDepsHash

When you change dependencies in package.json:

```bash
# 1. Update package.json
npm install axios@latest

# 2. Regenerate package-lock.json
npm install

# 3. Try building with Nix (will fail with new hash)
./nix.sh build-node-arm64

# 4. Copy the "got:" hash from error output
# 5. Update npmDepsHash in build.nix

# 6. Rebuild
./nix.sh build-node-arm64
```

### Docker Compose Configuration (docker-compose.yml)

```yaml
version: "3.8"

services:
  sui-price-oracle:
    # CRITICAL: Use image digest, not tag
    image: yourusername/sui-price-oracle@sha256:a1b2c3d4...
    container_name: sui-price-oracle
    restart: unless-stopped
    init: true
    network_mode: host
    volumes:
      - /app/ecdsa.sec:/app/ecdsa.sec:ro  # Signing key mounted by Oyster
```

**Critical**:
- **Use digest** (`@sha256:...`), never tags (`:latest`)
- Digest changes must be updated in docker-compose.yml
- Oyster generates signing key at `/app/ecdsa.sec`

---

## Deployment

### Automated Deployment Script

The repository includes `deploy.sh` that automates the entire process. Here's what it does:

#### Step 1: Deploy Smart Contracts

```bash
cd contracts
sui move build
sui client publish --gas-budget 100000000 --with-unpublished-dependencies

# Parse output for:
# - PACKAGE_ID
# - ENCLAVE_CONFIG_ID (shared EnclaveConfig object)
# - CAP_ID (owned Cap for PCR updates)
```

#### Step 2: Build and Deploy Enclave

```bash
# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    BUILD_ARCH="amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    BUILD_ARCH="arm64"
fi

# Build with Nix
./nix.sh build-node-$BUILD_ARCH

# Load and push to registry
docker load < ./node-$BUILD_ARCH-image.tar.gz
docker tag sui-price-oracle:node-reproducible-$BUILD_ARCH $REGISTRY/sui-price-oracle:latest
docker push $REGISTRY/sui-price-oracle:latest

# Get digest
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' $REGISTRY/sui-price-oracle:latest)

# Update docker-compose.yml with digest
sed -i "s|^[[:space:]]*image:.*|    image: $DIGEST|" enclave_node/docker-compose.yml

# Deploy to Oyster
oyster-cvm deploy \
  --wallet-private-key $PRIVATE_KEY \
  --docker-compose ./enclave_node/docker-compose.yml \
  --instance-type c6a.xlarge \
  --duration-in-minutes 60 \
  --arch amd64 \
  --deployment sui

# Extract PUBLIC_IP from output
```

#### Step 3: Register Enclave On-Chain

```bash
# Wait for enclave to be ready
sleep 10

# Get attestation document
curl http://$PUBLIC_IP:1301/attestation/hex

# Get PCR values
oyster-cvm verify --enclave-ip $PUBLIC_IP

# Extract PCR0, PCR1, PCR2, PCR16 from output

# Update PCRs in contract
sui client call \
  --package $PACKAGE_ID \
  --module enclave \
  --function update_pcrs \
  --args $ENCLAVE_CONFIG_ID $CAP_ID 0x$PCR0 0x$PCR1 0x$PCR2 0x$PCR16 \
  --type-args "$PACKAGE_ID::oyster_demo::OYSTER_DEMO" \
  --gas-budget 10000000

# Register enclave
bash contracts/script/register_enclave.sh \
  $PACKAGE_ID \
  $PACKAGE_ID \
  $ENCLAVE_CONFIG_ID \
  $PUBLIC_IP \
  oyster_demo \
  OYSTER_DEMO

# Extract ENCLAVE_ID from output
```

#### Step 4: Initialize Oracle

```bash
cd contracts/script
bash initialize_oracle.sh $PACKAGE_ID

# Extract ORACLE_ID from output
```

#### Step 5: Update Price

```bash
bash update_price.sh $PUBLIC_IP $PACKAGE_ID $ORACLE_ID $ENCLAVE_ID
```

### Manual Deployment

For step-by-step manual deployment:

```bash
# Export environment variables
export PRIVATE_KEY="suiprivkey..."
export DOCKER_REGISTRY="yourusername"

# Run automated script
./deploy.sh
```

The script saves all deployment info to `deployment.env`:

```bash
PACKAGE_ID=0x52af3e...
ENCLAVE_CONFIG_ID=0x4fb60b...
CAP_ID=0x85a3ef...
JOB_ID=100
PUBLIC_IP=13.233.177.31
DIGEST=yourusername/sui-price-oracle@sha256:f8fe29d2...
PCR0=3aa0e6e6ed7d8301...
PCR1=b0d319fa64f9c2c9...
PCR2=fdb2295dc5d9b67a...
PCR16=94a33ba1298c64a1...
ENCLAVE_ID=0x72c1a5...
ORACLE_ID=0x8d3f2b...
```

### Operational Commands

#### Debug Mode

For development and troubleshooting, deploy enclaves in debug mode to stream console logs:

```bash
# Deploy with debug flag
oyster-cvm deploy \
  --wallet-private-key $PRIVATE_KEY \
  --docker-compose ./enclave_node/docker-compose.yml \
  --duration-in-minutes 15 \
  --debug

# Logs will stream automatically during deployment
```

Explicitly stream logs from a running debug enclave:

```bash
# Stream logs from the beginning
oyster-cvm logs --ip $PUBLIC_IP --start-from 0
```

**Security Note**: Debug enclaves have PCRs set to zero, making them distinguishable from production enclaves. Never use debug mode for production deployments.

#### Managing Enclave Runtime

Extend or reduce enclave running time by managing funds:

**Deposit funds** (extend runtime):
```bash
# Add 0.02 USDC (amount in micro-units: 6 decimals)
oyster-cvm deposit \
  --wallet-private-key $PRIVATE_KEY \
  --job-id $JOB_ID \
  --amount 20000

# Check updated runtime
oyster-cvm list --address $YOUR_WALLET_ADDRESS
```

**Withdraw funds** (reduce runtime):
```bash
# Withdraw 0.01 USDC
oyster-cvm withdraw \
  --wallet-private-key $PRIVATE_KEY \
  --job-id $JOB_ID \
  --amount 10000

# Check updated runtime
oyster-cvm list --address $YOUR_WALLET_ADDRESS
```

**Note**: Required buffer amount prevents withdrawing too much. The job must maintain minimum funds.

#### List Active Jobs

View all active enclave jobs:

```bash
# List jobs for your wallet
oyster-cvm list --address $YOUR_WALLET_ADDRESS

# Output shows:
# - Job ID
# - Public IP
# - Instance type
# - Remaining time
# - Contract address (if using contract-based KMS)
```

---

## Verification

### Base Image Verification (PCR0, PCR1, PCR2)

Verify the Oyster base image by rebuilding from source:

```bash
# Launch Nix environment
docker run -it nixos/nix bash

# Inside container
git clone https://github.com/marlinprotocol/oyster-monorepo.git
cd oyster-monorepo && git checkout base-blue-v3.0.0

# Build enclave base image
nix build -vL \
  --extra-experimental-features nix-command \
  --extra-experimental-features flakes \
  --accept-flake-config \
  .#default.enclaves.blue.default

# View PCR values
cat result/pcr.json
```

Compare PCR0, PCR1, PCR2 with values from `oyster-cvm verify --enclave-ip $PUBLIC_IP`.

### Application Verification (PCR16/imageId)

Verify your application code:

```bash
# 1. Build Docker image
./nix.sh build-node-arm64

# 2. Load image
docker load < ./node-arm64-image.tar.gz

# 3. Get digest
docker images --digests --format '{{.Digest}}' sui-price-oracle:node-reproducible-arm64

# 4. Compare with docker-compose.yml
# Digest should match the sha256 hash in docker-compose.yml

# 5. Compute imageId
oyster-cvm compute-image-id --docker-compose ./enclave_node/docker-compose.yml

# 6. Compare with deployed enclave
oyster-cvm verify --enclave-ip $PUBLIC_IP

# imageId values should match exactly
```

**If imageId matches**: You have cryptographic proof that the deployed enclave is running the exact code you inspected locally.

---

## Testing

### Integration Test Flow

```bash
# 1. Test enclave health
curl http://$PUBLIC_IP:3000/health

# 2. Get enclave public key
curl http://$PUBLIC_IP:3000/public-key

# 3. Fetch signed price
curl http://$PUBLIC_IP:3000/price

# Response:
# {
#   "price": 2150000,
#   "timestamp_ms": 1738742400000,
#   "signature": "a1b2c3d4e5f6..."
# }

# 4. Submit to blockchain
bash contracts/script/update_price.sh $PUBLIC_IP $PACKAGE_ID $ORACLE_ID $ENCLAVE_ID

# 5. Query on-chain price
sui client call \
  --package $PACKAGE_ID \
  --module oyster_demo \
  --function get_latest_price \
  --args $ORACLE_ID \
  --type-args "$PACKAGE_ID::oyster_demo::OYSTER_DEMO"
```

### Query Historical Prices

```bash
# Get price at specific timestamp
sui client call \
  --package $PACKAGE_ID \
  --module oyster_demo \
  --function get_price_at_timestamp \
  --args $ORACLE_ID 1738742400000 \
  --type-args "$PACKAGE_ID::oyster_demo::OYSTER_DEMO"
```

### Verify Signature Locally

```javascript
import { verify, getPublicKey } from '@noble/secp256k1';
import { createHash } from 'crypto';
import { bcs } from '@mysten/bcs';

// Define structures
const PriceUpdatePayload = bcs.struct('PriceUpdatePayload', {
  price: bcs.u64(),
});

const IntentMessage = bcs.struct('IntentMessage', {
  intent: bcs.u8(),
  timestamp_ms: bcs.u64(),
  data: PriceUpdatePayload,
});

// Fetch signed price
const response = await fetch('http://$PUBLIC_IP:3000/price');
const { price, timestamp_ms, signature } = await response.json();

// Fetch public key
const pkResponse = await fetch('http://$PUBLIC_IP:3000/public-key');
const { public_key } = await pkResponse.json();

// Recreate signed message
const intentMessage = {
  intent: 0,
  timestamp_ms,
  data: { price },
};
const messageBytes = IntentMessage.serialize(intentMessage).toBytes();
const hash = createHash('sha256').update(messageBytes).digest();

// Verify signature
const isValid = verify(
  Buffer.from(signature, 'hex'),
  hash,
  Buffer.from(public_key, 'hex')
);

console.log('Signature valid:', isValid);
```

---

## Constraints and Best Practices

### Technical Constraints

#### 1. **secp256k1 Only**
- Sui's `ecdsa_k1` module only supports secp256k1 (not secp256r1/P-256)
- Use 64-byte compact signatures (r + s), not DER encoding
- Compressed public keys (33 bytes) preferred for storage efficiency

#### 2. **BCS Serialization**
- Must exactly match Move struct layout (field order matters)
- Use `@mysten/bcs` library for JavaScript
- IntentMessage wrapper prevents cross-context replay attacks

#### 3. **u64 Limits**
- Move's u64: 0 to 18,446,744,073,709,551,615
- For prices: use micro-units (6 decimals) = max $18,446,744.07
- For timestamps: Unix milliseconds fit in u64 until year 2262

#### 4. **Docker Image Digests**
- Always use `@sha256:...` digests in docker-compose.yml
- Tags (`:latest`) are mutable and break PCR verification
- Update digest after every rebuild

#### 5. **Oyster Resource Limits**
- Instance types: c6a.xlarge, c6g.xlarge (Graviton), etc.
- Duration: up to 24 hours per deployment
- Costs: paid in USDC on Sui blockchain

### Best Practices

#### 1. **Reproducible Builds**
- Use pure JavaScript libraries (no native modules)
- Commit all lock files (package-lock.json, flake.lock)
- Verify builds twice: `sha256sum image-run1.tar.gz image-run2.tar.gz`
- Build per-architecture if native code is unavoidable

#### 2. **Security**
- Never commit private keys to git
- Use Docker secrets for sensitive data
- Minimize enclave dependencies (reduce attack surface)
- Regularly update base images for security patches

#### 3. **Error Handling**
- Return HTTP 503 for API failures (not 500)
- Log all errors but don't expose internal details
- Implement retry logic for external API calls
- Validate all inputs before signing

#### 4. **Testing**
- Test signature verification locally before deployment
- Verify PCR values match expected hashes
- Run end-to-end integration tests
- Monitor enclave health endpoint

#### 5. **Gas Optimization**
- Batch multiple price updates if possible
- Use events instead of reading on-chain state
- Store only essential data on-chain
- Consider off-chain indexing for historical queries

### Common Pitfalls

#### ❌ **Native Dependencies**
Using native modules breaks reproducibility across architectures.
```json
// DON'T
"dependencies": {
  "secp256k1": "^5.0.0"  // Native module, architecture-specific
}

// DO
"dependencies": {
  "@noble/secp256k1": "^3.0.0"  // Pure JS, cross-platform
}
```

#### ❌ **Using Tags Instead of Digests**
```yaml
# DON'T
image: yourusername/sui-price-oracle:latest

# DO
image: yourusername/sui-price-oracle@sha256:a1b2c3d4...
```

#### ❌ **Forgetting to Update PCRs**
After rebuilding enclave, always:
1. Get new PCR values with `oyster-cvm verify`
2. Call `update_pcrs()` on EnclaveConfig
3. Re-register enclave with new attestation

#### ❌ **Not Verifying Reproducibility**
```bash
# Build twice and compare
./nix.sh build-node-arm64
cp node-arm64-image.tar.gz build1.tar.gz

./nix.sh build-node-arm64
cp node-arm64-image.tar.gz build2.tar.gz

# Hashes MUST match
sha256sum build1.tar.gz build2.tar.gz
```

#### ❌ **Incorrect BCS Serialization**
Field order must match Move struct exactly:
```javascript
// Move struct
public struct IntentMessage<T> has copy, drop {
    intent: u8,
    timestamp_ms: u64,
    data: T,
}

// JavaScript - field order MUST match
const IntentMessage = bcs.struct('IntentMessage', {
  intent: bcs.u8(),         // First
  timestamp_ms: bcs.u64(),  // Second
  data: DataType,           // Third
});
```

---

## Advanced Topics

### Multi-Enclave Support

To support multiple enclave instances:

1. **Shared EnclaveConfig**: All instances use same PCRs
2. **Individual Enclave Objects**: Each instance registers separately
3. **Load Balancing**: Round-robin across enclave IPs

```bash
# Register multiple enclaves
for IP in $ENCLAVE_IP_1 $ENCLAVE_IP_2 $ENCLAVE_IP_3; do
  bash register_enclave.sh $PACKAGE_ID $PACKAGE_ID $ENCLAVE_CONFIG_ID $IP oyster_demo OYSTER_DEMO
done
```

### Price Feed Aggregation

Aggregate prices from multiple sources:

```javascript
async function fetchAggregatedPrice() {
  const sources = [
    'https://api.coingecko.com/api/v3/simple/price?ids=sui&vs_currencies=usd',
    'https://api.coinbase.com/v2/prices/SUI-USD/spot',
    'https://api.binance.com/api/v3/ticker/price?symbol=SUIUSDT',
  ];

  const prices = await Promise.all(
    sources.map(async (url) => {
      const response = await axios.get(url);
      return parsePrice(response.data);  // Parse source-specific format
    })
  );

  // Median price
  prices.sort((a, b) => a - b);
  return prices[Math.floor(prices.length / 2)];
}
```

### Custom Data Types

Extend the pattern to any data type:

```move
// Custom payload
public struct WeatherPayload has copy, drop {
    temperature: u64,
    humidity: u64,
    location: String,
}

// Update function
fun update_weather<T: drop>(
    oracle: &mut WeatherOracle<T>,
    enclave: &Enclave<T>,
    temperature: u64,
    humidity: u64,
    location: String,
    timestamp_ms: u64,
    signature: vector<u8>,
) {
    // Verify signature...
    // Store data...
}
```

### Upgrading Enclave Code

When updating enclave application:

```bash
# 1. Build new image
./nix.sh build-node-arm64

# 2. Get new PCR16 value
oyster-cvm compute-image-id --docker-compose ./enclave_node/docker-compose.yml

# 3. Update PCRs on-chain
sui client call \
  --package $PACKAGE_ID \
  --module enclave \
  --function update_pcrs \
  --args $ENCLAVE_CONFIG_ID $CAP_ID 0x$PCR0 0x$PCR1 0x$PCR2 0x$NEW_PCR16 \
  --type-args "$PACKAGE_ID::oyster_demo::OYSTER_DEMO"

# 4. Deploy new enclave
oyster-cvm deploy ...

# 5. Register new enclave instance
bash register_enclave.sh ...
```

### Key Management Strategies

Oyster provides three approaches to managing signing keys in enclaves, each with different trade-offs:

#### 1. Ephemeral Keys (Current Implementation)

**What it is**: Keys automatically generated on enclave startup, available at standard paths.

**Available Keys**:
- `secp256k1`: `/app/ecdsa.sec` (private), `/app/ecdsa.pub` (public)
- `x25519`: `/app/id.sec` (private), `/app/id.pub` (public)

**Characteristics**:
- ✅ Simple to use, no additional setup
- ✅ Each deployment gets fresh keys
- ❌ Keys change on restart or redeployment
- ❌ Cannot maintain persistent wallets or encrypted state

**Use Cases**:
- Temporary oracles or testing
- Applications that don't need persistent identity
- Proof-of-concept implementations

**Example** (current implementation in src/index.js:96-112):
```javascript
function loadSigningKeyFromFile(path) {
  const keyBytes = fs.readFileSync(path);
  if (keyBytes.length !== 32) {
    throw new Error(`Expected 32-byte secp256k1 private key, got ${keyBytes.length} bytes`);
  }
  try {
    getPublicKey(keyBytes);
  } catch (error) {
    throw new Error('Invalid secp256k1 private key');
  }
  return keyBytes;
}

// Usage
const keyPath = '/app/ecdsa.sec';  // Oyster-provided ephemeral key
signingKey = loadSigningKeyFromFile(keyPath);
```

#### 2. Image-Based Persistent Keys (KMS Derive)

**What it is**: Keys derived from Nautilus KMS based on enclave's image ID, persisting across restarts.

**KMS Endpoint**: `http://127.0.0.1:1100/derive/{key_type}?path={derivation_path}`

**Characteristics**:
- ✅ Keys persist across enclave restarts
- ✅ Same keys for identical enclave deployments
- ✅ Automatic key derivation, no external storage
- ❌ Keys change when code changes (new image ID)
- ❌ Difficult to upgrade application while keeping same keys

**Use Cases**:
- Production oracles with stable codebase
- Long-running services with persistent wallets
- Applications needing deterministic key derivation

**Implementation**:

Modify src/index.js to fetch key from KMS:
```javascript
import axios from 'axios';

async function loadSigningKeyFromKMS(derivationPath) {
  const kmsUrl = `http://127.0.0.1:1100/derive/secp256k1?path=${derivationPath}`;

  try {
    const response = await axios.get(kmsUrl, {
      responseType: 'arraybuffer'
    });

    const keyBytes = new Uint8Array(response.data).slice(0, 32);

    if (keyBytes.length !== 32) {
      throw new Error(`Expected 32-byte key from KMS, got ${keyBytes.length} bytes`);
    }

    // Validate key
    getPublicKey(keyBytes);

    return keyBytes;
  } catch (error) {
    console.error('Failed to fetch key from KMS:', error.message);
    throw error;
  }
}

// Usage in main()
async function main() {
  console.log('Loading secp256k1 signing key from KMS...');
  signingKey = await loadSigningKeyFromKMS('sui-price-oracle');
  console.log('Signing key loaded successfully from KMS');

  const publicKey = getPublicKey(signingKey, true);
  console.log(`Public key (hex): ${Buffer.from(publicKey).toString('hex')}`);

  // Start server...
}
```

Update docker-compose.yml (remove volume mount):
```yaml
services:
  sui-price-oracle:
    image: yourusername/sui-price-oracle@sha256:...
    container_name: sui-price-oracle
    restart: unless-stopped
    init: true
    network_mode: host
    # No volumes needed - KMS provides keys
```

**Verification**:
```bash
# Get expected public key from KMS (off-chain)
oyster-cvm kms-derive \
  --image-id <IMAGE_ID> \
  --path sui-price-oracle \
  --key-type secp256k1/public

# Compare with public key from enclave
curl http://$PUBLIC_IP:3000/public-key
```

**Important**: Image ID changes with any code modification. To update code:
1. Build new image → new image ID
2. Deploy with new image ID → new keys
3. Re-register enclave with new public key on-chain

#### 3. Contract-Based Persistent Keys (Upgradeable)

**What it is**: Keys derived from KMS based on smart contract approval, allowing multiple image IDs to share same keys.

**KMS Endpoint**: `http://127.0.0.1:1101/derive/{key_type}?path={derivation_path}`

**Characteristics**:
- ✅ Keys persist across code updates
- ✅ Approve multiple image IDs for same keys
- ✅ Flexible upgrade path for applications
- ✅ On-chain access control via smart contracts
- ⚠️ Requires deploying and managing verifier contract
- ⚠️ More complex deployment workflow

**Use Cases**:
- Production oracles requiring code updates
- Applications with persistent wallets that need upgrades
- Multi-version deployments with shared identity

**Implementation**:

Step 1: Modify src/index.js to use contract-based KMS (port 1101):
```javascript
async function loadSigningKeyFromContractKMS(derivationPath) {
  // Note: port 1101 instead of 1100
  const kmsUrl = `http://127.0.0.1:1101/derive/secp256k1?path=${derivationPath}`;

  try {
    const response = await axios.get(kmsUrl, {
      responseType: 'arraybuffer'
    });

    const keyBytes = new Uint8Array(response.data).slice(0, 32);

    if (keyBytes.length !== 32) {
      throw new Error(`Expected 32-byte key from KMS, got ${keyBytes.length} bytes`);
    }

    getPublicKey(keyBytes);
    return keyBytes;
  } catch (error) {
    console.error('Failed to fetch key from contract KMS:', error.message);
    throw error;
  }
}

// Usage
signingKey = await loadSigningKeyFromContractKMS('sui-price-oracle');
```

Step 2: Deploy KmsVerifiable contract:
```bash
# Deploy verifier contract on Arbitrum One
oyster-cvm kms-contract deploy --wallet-private-key $PRIVATE_KEY

# Save CONTRACT_ADDRESS from output
CONTRACT_ADDRESS=0x1234...
```

Step 3: Approve initial image ID:
```bash
# Compute image ID for your enclave
oyster-cvm compute-image-id \
  --contract-address $CONTRACT_ADDRESS \
  --chain-id 42161 \
  --docker-compose ./enclave_node/docker-compose.yml

# Approve image ID in contract
oyster-cvm kms-contract approve \
  --wallet-private-key $PRIVATE_KEY \
  --image-id $IMAGE_ID \
  --contract-address $CONTRACT_ADDRESS
```

Step 4: Deploy enclave with contract parameters:
```bash
oyster-cvm deploy \
  --wallet-private-key $PRIVATE_KEY \
  --contract-address $CONTRACT_ADDRESS \
  --chain-id 42161 \
  --duration-in-minutes 60 \
  --docker-compose ./enclave_node/docker-compose.yml
```

Step 5: Get public key (consistent across approved image IDs):
```bash
# Get expected public key from KMS
oyster-cvm kms-derive \
  --contract-address $CONTRACT_ADDRESS \
  --chain-id 42161 \
  --path sui-price-oracle \
  --key-type secp256k1/public

# Verify matches enclave
curl http://$PUBLIC_IP:3000/public-key
```

**Upgrading with Contract-Based KMS**:

When you need to update enclave code:

```bash
# 1. Build new image with changes
./nix.sh build-node-arm64
docker load < ./node-arm64-image.tar.gz
docker tag sui-price-oracle:node-reproducible-arm64 $REGISTRY/sui-price-oracle:v2
docker push $REGISTRY/sui-price-oracle:v2

# 2. Update docker-compose.yml with new digest
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' $REGISTRY/sui-price-oracle:v2)
sed -i "s|^[[:space:]]*image:.*|    image: $DIGEST|" enclave_node/docker-compose.yml

# 3. Compute NEW image ID
NEW_IMAGE_ID=$(oyster-cvm compute-image-id \
  --contract-address $CONTRACT_ADDRESS \
  --chain-id 42161 \
  --docker-compose ./enclave_node/docker-compose.yml)

# 4. Approve NEW image ID (SAME contract = SAME keys!)
oyster-cvm kms-contract approve \
  --wallet-private-key $PRIVATE_KEY \
  --image-id $NEW_IMAGE_ID \
  --contract-address $CONTRACT_ADDRESS

# 5. Deploy new version
oyster-cvm deploy \
  --wallet-private-key $PRIVATE_KEY \
  --contract-address $CONTRACT_ADDRESS \
  --chain-id 42161 \
  --duration-in-minutes 60 \
  --docker-compose ./enclave_node/docker-compose.yml

# 6. Verify SAME public key as before
curl http://$NEW_PUBLIC_IP:3000/public-key

# Keys are identical! No need to re-register enclave on Sui blockchain
```

**Contract Management**:
```bash
# List approved image IDs
oyster-cvm kms-contract list --contract-address $CONTRACT_ADDRESS

# Revoke an old image ID
oyster-cvm kms-contract revoke \
  --wallet-private-key $PRIVATE_KEY \
  --image-id $OLD_IMAGE_ID \
  --contract-address $CONTRACT_ADDRESS
```

#### Comparison Table

| Feature | Ephemeral Keys | Image-Based KMS | Contract-Based KMS |
|---------|----------------|-----------------|-------------------|
| **Persistence** | ❌ Changes per deployment | ✅ Persists for same image | ✅ Persists across updates |
| **Setup Complexity** | Simple | Moderate | Complex |
| **Code Updates** | Easy (new keys) | Hard (new keys) | Easy (same keys) |
| **On-chain Registration** | Every deployment | Every code change | Once per contract |
| **External Dependencies** | None | None | Arbitrum contract |
| **Cost** | Lowest | Low | Moderate (contract deploy) |
| **Best For** | Testing, PoCs | Stable production | Upgradeable production |

#### Recommendation

**For this demo**: Ephemeral keys are sufficient and simplify the deployment.

**For production**:
- Start with **Image-Based KMS** if you have stable code
- Upgrade to **Contract-Based KMS** when you need to update application logic while maintaining the same on-chain identity

**Migration Path**:
1. Deploy with ephemeral keys (current implementation)
2. Add image-based KMS when stability is needed
3. Add contract-based KMS when upgradeability is required

Each migration requires re-registering the enclave on-chain with the new public key, so plan accordingly.

---

## Troubleshooting

### Issue: "Invalid signature" error

**Cause**: BCS serialization mismatch between enclave and Move contract.

**Solution**:
1. Verify field order matches exactly
2. Check data types (u8, u64) are correct
3. Ensure IntentMessage wrapper structure matches
4. Test serialization locally before deployment

### Issue: PCR verification fails

**Cause**: Image digest in docker-compose.yml doesn't match pushed image.

**Solution**:
```bash
# 1. Get actual digest from registry
docker pull $REGISTRY/sui-price-oracle:latest
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' $REGISTRY/sui-price-oracle:latest)

# 2. Update docker-compose.yml
sed -i "s|^[[:space:]]*image:.*|    image: $DIGEST|" enclave_node/docker-compose.yml

# 3. Redeploy
oyster-cvm deploy ...
```

### Issue: Enclave health check fails

**Cause**: Enclave not fully initialized or network issues.

**Solution**:
```bash
# Wait longer
sleep 30

# Check Oyster logs
oyster-cvm logs --job-id $JOB_ID

# Test connectivity
curl -v http://$PUBLIC_IP:3000/health
```

### Issue: "npmDepsHash mismatch" during Nix build

**Cause**: package-lock.json changed but npmDepsHash not updated.

**Solution**:
```bash
# Let Nix fail and show new hash
./nix.sh build-node-arm64

# Copy "got: sha256-..." from error output
# Update npmDepsHash in build.nix
# Rebuild
```

---

## Resources

### Documentation

- **Sui Documentation**: https://docs.sui.io/
- **Nautilus Framework**: https://github.com/MystenLabs/nautilus
- **Oyster Documentation**: https://docs.marlin.org/oyster/
- **Oyster CVM CLI**: https://docs.marlin.org/oyster/build-cvm/quickstart
- **AWS Nitro Enclaves**: https://aws.amazon.com/ec2/nitro/nitro-enclaves/
- **Nix Flakes**: https://nixos.wiki/wiki/Flakes

### Libraries

- **@mysten/bcs**: BCS serialization for Move compatibility
- **@noble/secp256k1**: Pure JS secp256k1 implementation
- **@noble/hashes**: Cryptographic hashing (SHA256)
- **Express.js**: Node.js HTTP framework
- **Axios**: HTTP client for API requests

### Community

- **Sui Discord**: https://discord.gg/sui
- **Marlin Discord**: https://discord.gg/marlin
- **Nautilus GitHub**: https://github.com/MystenLabs/nautilus/discussions

---

## License

This guide and associated code are licensed under Apache-2.0.

## Credits

- **Marlin Protocol**: Oyster TEE infrastructure
- **Mysten Labs**: Sui blockchain and Nautilus framework
- **AWS**: Nitro Enclaves hardware security

---

## Appendix: Complete File Structure

```
.
├── contracts/
│   ├── sources/
│   │   ├── oyster_demo.move         # Price oracle implementation
│   │   └── enclave.move             # Enclave registration system
│   ├── script/
│   │   ├── initialize_oracle.sh     # Create oracle object
│   │   ├── register_enclave.sh      # Register enclave on-chain
│   │   ├── update_price.sh          # Submit signed price
│   │   ├── get_price.sh             # Query oracle
│   │   └── query_enclave.sh         # Test enclave connectivity
│   ├── Move.toml                    # Move package config
│   ├── Move.lock                    # Move dependencies lock
│   └── README.md
│
├── enclave_node/
│   ├── src/
│   │   └── index.js                 # Express.js HTTP server
│   ├── package.json                 # Node.js dependencies
│   ├── package-lock.json            # Locked dependency versions
│   ├── Dockerfile                   # Multi-stage Docker build
│   ├── docker-compose.yml           # Oyster deployment config
│   ├── build.nix                    # Nix build configuration
│   └── README.md
│
├── flake.nix                        # Root Nix flakes config
├── flake.lock                       # Nix dependencies lock
├── nix.sh                           # Nix build helper script
├── deploy.sh                        # Automated deployment script
├── deployment.env                   # Deployment state (generated)
├── README.md                        # Project overview
├── GUIDE.md                         # This file
└── .gitignore
```

---

**End of Guide**

This comprehensive guide covers all aspects of building Marlin Oyster applications for Sui Nautilus with Node.js. Use it as a reference to create your own TEE-based decentralized applications with verifiable execution and cryptographic attestation.
