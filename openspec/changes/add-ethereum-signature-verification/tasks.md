# Implementation Tasks

## 1. Move Contract - Add Helper Functions

- [ ] 1.1 Add error codes (`EInvalidEthereumSignature`, `EEthereumAddressMismatch`, `EInvalidSignatureLength`)
- [ ] 1.2 Implement `u64_to_string(value: u64): String` - Convert u64 to ASCII string
- [ ] 1.3 Implement `construct_eth_message(score, timestamp_ms, wallet_address): vector<u8>` - Build message user signed
- [ ] 1.4 Implement `apply_eip191_prefix(message): vector<u8>` - Add Ethereum personal_sign prefix
- [ ] 1.5 Implement `verify_ethereum_signature(message, signature): vector<u8>` - Recover address from signature using `secp256k1_ecrecover`
- [ ] 1.6 Implement `ethereum_address_matches(recovered_bytes, claimed_string): bool` - Case-insensitive hex comparison
- [ ] 1.7 Add helper functions `nibble_to_hex_char` and `to_lowercase` for address comparison

## 2. Move Contract - Refactor Verification Logic

- [ ] 2.1 Simplify `update_score` internal function - Remove all signature verification, only store data
- [ ] 2.2 Rewrite `update_wallet_score` entry function - Add `eth_signature: vector<u8>` parameter
- [ ] 2.3 Move TEE signature verification from `update_score` to `update_wallet_score`
- [ ] 2.4 Add Ethereum signature verification to `update_wallet_score` using helper functions
- [ ] 2.5 Ensure both signatures are validated before calling simplified `update_score`

## 3. Testing

- [ ] 3.1 Create `oracle/contracts/tests/signature_tests.move` test file
- [ ] 3.2 Add test for `u64_to_string` with values: 0, 42, 850, 1707220800000
- [ ] 3.3 Add test for `construct_eth_message` verifying exact output format
- [ ] 3.4 Add test for EIP-191 prefix application
- [ ] 3.5 Add test for address comparison (case-insensitive)
- [ ] 3.6 Run `sui move build` to verify compilation
- [ ] 3.7 Run `sui move test` to verify all tests pass

## 4. Deployment Script Updates

- [ ] 4.1 Add check for `cast` tool availability at script start
- [ ] 4.2 Add logic to construct message string from oracle response
- [ ] 4.3 Add `cast wallet sign --no-hash "$MESSAGE"` call to generate Ethereum signature
- [ ] 4.4 Add Python conversion of Ethereum signature to vector<u8> format
- [ ] 4.5 Update `sui client call` arguments to include `$ETH_SIG_VECTOR` as 7th parameter
- [ ] 4.6 Test script with local Ethereum wallet (via cast + private key)

## 5. Documentation

- [ ] 5.1 Document message format in contract comments
- [ ] 5.2 Update `oracle/CLAUDE.md` with signature verification details
- [ ] 5.3 Add README section explaining how to use `cast wallet sign`
- [ ] 5.4 Document breaking change and migration path

## 6. Integration Testing

- [ ] 6.1 Deploy to Sui testnet
- [ ] 6.2 Test successful submission with matching Ethereum wallet
- [ ] 6.3 Test rejection with wrong wallet (verify `EEthereumAddressMismatch` error)
- [ ] 6.4 Test rejection with malformed signature (verify `EInvalidSignatureLength` error)
- [ ] 6.5 Test rejection with invalid TEE signature (verify `EInvalidSignature` error)
- [ ] 6.6 Query stored score to verify data integrity
