# Proposal: Add Deterministic Seeding to Oracle AI Scoring

## Problem Statement

The oracle currently generates AI scores without deterministic control:

1. **Non-Reproducible Scores**: Scoring the same wallet multiple times may produce different results (even with temperature=0.3)
2. **No Seed Parameter**: Ollama's `seed` option is not used, missing an opportunity for better consistency
3. **Temperature Too High**: Current temperature of 0.3 allows more variance than necessary for creditworthiness scoring

This leads to:
- Users potentially getting different scores for the same wallet if they retry
- Difficulty debugging score inconsistencies
- Reduced trust in score stability

While temperature=0 and seed don't guarantee 100% reproducibility due to platform quirks (floating-point precision, GPU non-determinism), using wallet address as seed significantly improves consistency for repeated scoring of the same wallet.

## Proposed Solution

Implement deterministic seeding based on wallet address:

1. **Hash Wallet Address**: Use SHA-256 to hash the lowercase wallet address
2. **Extract Seed**: Use first 4 bytes of hash as 32-bit unsigned integer seed
3. **Pass to Ollama**: Provide seed via `options.seed` parameter
4. **Reduce Temperature**: Lower from 0.3 to 0.1 for better determinism

This ensures:
- Same wallet always gets the same seed
- First-run inconsistencies minimized (common with Ollama)
- Subsequent runs for same wallet are highly consistent
- Different wallets get different seeds (no score correlation)

## User Impact

**Protocol Users:**
- Consistent scores when re-evaluating the same wallet
- Predictable score updates (only change when on-chain data changes)
- Higher trust in score stability

**Developers:**
- Easier debugging (reproducible AI behavior for same input)
- Deterministic testing with known wallet addresses
- Reduced variance in integration tests

**Oracle Operators:**
- Lower complaint rate about "score changed without reason"
- Easier audit trails (same input → same output)
- Better cache efficiency (can cache by wallet address)

## Technical Approach

### Seed Generation

```javascript
import { createHash } from 'crypto';

function generateSeedFromAddress(address) {
  // Normalize address (lowercase, strip 0x prefix if present)
  const normalized = address.toLowerCase().replace(/^0x/, '');

  // Hash to 32 bytes
  const hash = createHash('sha256')
    .update(normalized)
    .digest();

  // Use first 4 bytes as unsigned 32-bit integer
  return hash.readUInt32BE(0);
}
```

### Ollama Integration

```javascript
const response = await ollamaClient.generate({
  model: 'llama3.2:1b',
  prompt,
  format: AI_RESPONSE_SCHEMA,
  options: {
    temperature: 0.1,  // Reduced from 0.3
    num_predict: 800,
    seed: generateSeedFromAddress(walletAddress)  // Deterministic
  }
});
```

### Dependencies

- No new dependencies (uses existing `crypto` module from Node.js stdlib)

### Performance Impact

- **Hashing overhead**: +5-10ms per request (negligible)
- **Inference change**: No latency impact from seed parameter
- **Temperature reduction**: Slightly faster inference (~50-100ms saved)
- **Net impact**: Negligible or slight improvement

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Not 100% deterministic | Users expect perfect reproducibility | Document limitations, explain 90%+ consistency |
| Temperature too low | Less creative reasoning | 0.1 is standard for factual tasks; monitor quality |
| Seed collisions | Different wallets get same seed | SHA-256 makes collisions astronomically unlikely |
| Ollama seed unsupported | Feature doesn't work | Gracefully degrade (seed is optional parameter) |

## Success Metrics

- **Reproducibility rate**: >90% same score for same wallet across 10 runs
- **Score variance**: Std dev <20 points for same wallet (down from current ~50-80)
- **Temperature impact**: No quality degradation at 0.1 vs 0.3
- **Latency**: No regression (target: +5-10ms)

## Related Changes

- Complements `add-json-schema-validation-oracle`: Determinism + validation = high reliability
- Complements `add-few-shot-prompting-oracle`: Better prompts + determinism = best consistency
- Independent of `add-prompt-versioning-oracle`: Can implement in any order
