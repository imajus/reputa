# Change: Add Ethereum Signature Verification to Score Oracle

## Why

The current `update_wallet_score` entry function accepts any Ethereum address and score without verifying that the transaction submitter owns the Ethereum address being scored. This creates a security vulnerability where anyone can submit fraudulent reputation scores for addresses they don't control.

This undermines the core trust model of the system, as malicious actors could:
- Submit high scores for addresses they don't own to falsely inflate reputation
- Submit low scores to damage competitors' reputations
- Manipulate the reputation system without consequences

## What Changes

Add dual signature verification to the Move smart contract:

1. **TEE Signature Verification** (existing, relocated) - Proves the score was correctly calculated by the trusted oracle enclave
2. **Ethereum Wallet Signature Verification** (new) - Proves the user owns the Ethereum address being scored

The implementation uses Sui's `secp256k1_ecrecover` with Keccak256 hashing to verify EIP-191 formatted Ethereum signatures, following the standard used by MetaMask, Rainbow, and other Ethereum wallets.

**Key Technical Changes:**
- Add 5 helper functions to `score_oracle.move` for Ethereum signature verification
- Move TEE signature verification from `update_score` internal function to `update_wallet_score` entry function
- Simplify `update_score` to only store validated data (no verification logic)
- Update `update_score.sh` deployment script to generate Ethereum signatures using Foundry's `cast` tool
- Add Move unit tests for message construction and signature verification

**Breaking Change:** This modifies the `update_wallet_score` entry function signature to require an additional `eth_signature: vector<u8>` parameter.

## Impact

**Affected specs:**
- `score-oracle` (new capability spec)

**Affected code:**
- `oracle/contracts/sources/score_oracle.move` - Core smart contract
- `oracle/contracts/script/update_score.sh` - CLI deployment script
- `oracle/contracts/tests/signature_tests.move` - New test file

**Frontend integration:** Out of scope for this change. Frontend signature capture will be implemented separately when Sui wallet integration is ready.

**Gas cost impact:** ~3800 additional gas units (~0.005-0.008 SUI increase per transaction)
