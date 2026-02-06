# Technical Design: Ethereum Signature Verification

## Context

The Reputa oracle currently validates scores using only a TEE (Trusted Execution Environment) signature, which proves the score was correctly calculated. However, there's no verification that the transaction submitter owns the Ethereum address being scored, allowing anyone to submit scores for any address.

The system consists of:
- **Move smart contracts** on Sui blockchain (`oracle/contracts/sources/score_oracle.move`)
- **Node.js enclave** running in TEE (`oracle/app/src/index.js`)
- **Bash deployment scripts** for testing and production (`oracle/contracts/script/`)

Current signature flow:
```
Oracle API → Calculate score → Sign with TEE key (SHA256) → Submit to Sui → Verify TEE signature
```

## Goals / Non-Goals

**Goals:**
- Prevent unauthorized score submissions by requiring proof of Ethereum wallet ownership
- Maintain existing TEE signature verification (dual verification model)
- Use industry-standard EIP-191 message signing (compatible with MetaMask, Rainbow, etc.)
- Keep implementation simple and gas-efficient
- Support CLI testing with Foundry's `cast` tool

**Non-Goals:**
- Frontend browser wallet integration (separate future work)
- Signature caching or replay protection beyond timestamp validation
- Support for EIP-712 typed structured data (stick with simpler EIP-191)
- Multi-signature or threshold signatures

## Decisions

### Decision 1: Dual Signature Model

**Choice:** Require BOTH TEE signature and Ethereum signature

**Alternatives considered:**
1. Only Ethereum signature - Simpler but loses TEE score integrity verification
2. Replace TEE with Ethereum - Would require major architecture changes
3. Make Ethereum signature optional - Defeats security purpose

**Rationale:** Dual signatures provide defense-in-depth:
- TEE signature proves score was correctly calculated by authorized oracle
- Ethereum signature proves user owns the address being scored
- Both are necessary: TEE alone allows forgery, Ethereum alone removes oracle trust model

### Decision 2: EIP-191 Message Format

**Choice:** Use EIP-191 personal_sign format with structured message

**Message template:**
```
Reputa Score Authorization
Score: {score}
Timestamp: {timestamp_ms}
Address: {wallet_address}
```

**Alternatives considered:**
1. EIP-712 typed structured data - More complex, requires domain separator
2. Raw signature without prefix - Not compatible with standard wallets
3. Just sign the address - Lacks replay protection and score binding

**Rationale:**
- EIP-191 is the standard for `personal_sign` in MetaMask/Rainbow/etc
- Human-readable message improves user trust
- Including score and timestamp prevents signature reuse
- Simpler than EIP-712 while providing adequate security

### Decision 3: Signature Verification in Entry Function

**Choice:** Move ALL signature verification to `update_wallet_score` entry function; simplify `update_score` to data storage only

**Alternatives considered:**
1. Keep verification in `update_score` - More complex internal function
2. Create separate verification function - Additional function call overhead
3. Verify in two stages - Split logic increases complexity

**Rationale:**
- Entry function is the security boundary - validate inputs there
- Internal `update_score` becomes pure data storage
- Easier to test and reason about
- Follows principle of separation: entry = validate, internal = execute

### Decision 4: Use `secp256k1_ecrecover` with Keccak256

**Choice:** Use Sui's built-in `secp256k1_ecrecover` with Keccak256 hash (flag=0)

**Technical details:**
- Ethereum signatures: 65 bytes (r: 32, s: 32, v: 1)
- TEE signatures: 64 bytes (r: 32, s: 32) with SHA256
- Different hash functions: Keccak256 for Ethereum, SHA256 for TEE
- Recovery ID normalization: Ethereum uses 27/28, Sui expects 0/1

**Alternatives considered:**
1. Use `secp256k1_verify` - Requires knowing public key upfront
2. Manual public key derivation - More complex, error-prone
3. Different signature format - Would break wallet compatibility

**Rationale:**
- `ecrecover` derives address directly from signature
- Matches Ethereum's standard signature verification
- Sui framework provides native support
- Keccak256 is required for Ethereum compatibility

### Decision 5: CLI Signature with Foundry `cast`

**Choice:** Generate Ethereum signatures in `update_score.sh` using `cast wallet sign`

**Implementation:**
```bash
MESSAGE="Reputa Score Authorization\n..."
ETH_SIGNATURE=$(cast wallet sign --no-hash "$MESSAGE")
```

**Alternatives considered:**
1. Manual signature with ethers.js script - Requires Node.js, more complex
2. Require pre-generated signature as parameter - Poor UX, error-prone
3. Use Python with web3.py - Additional dependency

**Rationale:**
- Foundry is standard Ethereum development toolchain
- `cast wallet sign` handles EIP-191 prefix automatically
- Supports multiple key sources (env var, keystore, hardware wallet)
- Same tool chain as production Ethereum workflows
- No additional CLI arguments needed

### Decision 6: Case-Insensitive Address Comparison

**Choice:** Implement case-insensitive hex comparison in Move

**Rationale:**
- Ethereum addresses can be checksummed (mixed case) or lowercase
- Users might input either format
- Move needs manual case normalization (no built-in string lowercase)
- Compare byte-by-byte with `to_lowercase` helper

## Risks / Trade-offs

### Risk 1: Message Format Mismatch

**Risk:** Bash script and Move contract construct different messages

**Impact:** Signature verification always fails, system unusable

**Mitigation:**
- Unit test both message construction implementations
- Document exact format prominently
- Add integration test comparing outputs
- Consider future: add `/preview-message` oracle endpoint for validation

**Trade-off:** Accept manual testing burden for simplicity over complex validation infrastructure

### Risk 2: Gas Cost Increase

**Risk:** Additional cryptographic operations increase transaction costs

**Quantification:**
- Message construction: ~100 gas
- Keccak256 hashing: ~500 gas
- secp256k1_ecrecover: ~3000 gas
- Address comparison: ~200 gas
- **Total increase:** ~3800 gas (~0.005-0.008 SUI)

**Mitigation:** Acceptable cost for security guarantee

**Trade-off:** Accept higher gas cost for preventing forgery attacks

### Risk 3: Foundry Dependency

**Risk:** Users must install Foundry to use deployment script

**Impact:** Additional setup friction for testing/deployment

**Mitigation:**
- Document installation clearly
- Foundry is widely adopted standard tool
- One-line install: `curl -L https://foundry.paradigm.xyz | bash`
- Script checks for `cast` availability upfront

**Trade-off:** Accept dependency for better UX than manual signature generation

### Risk 4: Breaking Change

**Risk:** Existing deployment scripts and workflows break

**Impact:** Requires coordinated upgrade

**Mitigation:**
- Clear documentation of breaking change
- Old scores remain readable (read path unchanged)
- New write path requires update
- Frontend integration deferred to separate change

**Trade-off:** Accept one-time migration cost for security improvement

## Migration Plan

### Phase 1: Smart Contract Deployment

1. Build and test new contract locally
2. Deploy to Sui testnet with test wallet
3. Run integration tests
4. Deploy to mainnet
5. Publish new PACKAGE_ID

### Phase 2: Script Update

1. Update `update_score.sh` with new logic
2. Test with Ethereum test wallet
3. Document Foundry setup in README
4. Update deployment documentation

### Phase 3: Future Frontend Integration

(Out of scope for this change)

1. Add signature capture to frontend (ScoreReview page)
2. Update WalletConnect transaction submission
3. Add Ethereum signature to ReputaContext state

## Open Questions

**Q: Should we add nonce-based replay protection?**

A: No for initial implementation. Timestamp provides basic replay protection. Nonce table adds storage cost and complexity. Can add later if needed.

**Q: What if user signs with wrong wallet?**

A: Transaction fails with `EEthereumAddressMismatch`. Clear error, user can retry with correct wallet. Script should validate signing wallet matches target address before submission.

**Q: How to handle signature expiration?**

A: Oracle returns timestamp in response. Signatures are bound to that timestamp. Optional future enhancement: add timestamp freshness check in contract (e.g., must be within 1 hour).

**Q: Should we support EIP-712?**

A: Not now. EIP-191 is simpler and sufficient. EIP-712 requires domain separator and typed data structure. Can add in future if user feedback indicates need.
