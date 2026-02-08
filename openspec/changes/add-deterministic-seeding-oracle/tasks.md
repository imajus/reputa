# Tasks: Add Deterministic Seeding to Oracle AI Scoring

## Implementation Tasks

- [ ] Create generateSeedFromAddress() function using crypto.createHash
- [ ] Normalize wallet address (lowercase, strip 0x prefix)
- [ ] Hash address with SHA-256
- [ ] Extract first 4 bytes as unsigned 32-bit integer
- [ ] Pass seed to Ollama via options.seed parameter
- [ ] Reduce temperature from 0.3 to 0.1
- [ ] Ensure seed parameter gracefully degrades if unsupported

## Testing Tasks

- [ ] Test seed generation with various address formats (0x prefix, no prefix, mixed case)
- [ ] Verify same address always produces same seed
- [ ] Verify different addresses produce different seeds
- [ ] Test reproducibility: score same wallet 10 times, measure variance
- [ ] Compare variance at temp=0.1 vs temp=0.3
- [ ] Measure hashing overhead (should be <10ms)
- [ ] Test with production Ollama version (0.10.1+)

## Validation Tasks

- [ ] Verify reproducibility rate >90% for same wallet
- [ ] Verify score std dev <20 points for same wallet
- [ ] Verify no quality degradation at temp=0.1 vs 0.3
- [ ] Verify no latency regression
- [ ] Check seed collisions (test 10,000 random addresses)
- [ ] Verify backward compatibility (signature format unchanged)

## Documentation Tasks

- [ ] Document seed generation algorithm
- [ ] Explain reproducibility limitations (not 100% guaranteed)
- [ ] Add logging: include seed value in debug logs
- [ ] Update oracle/CLAUDE.md with seeding behavior
- [ ] Document temperature reduction rationale
