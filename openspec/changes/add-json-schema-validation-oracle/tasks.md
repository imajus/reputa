# Tasks: Add JSON Schema Validation and Retry Logic to Oracle

## Implementation Tasks

- [ ] Add ajv dependency to package.json
- [ ] Define AI_RESPONSE_SCHEMA constant in oracle/app/src/index.js
- [ ] Create generateAIScoreWithValidation() function with retry loop
- [ ] Implement temperature decay logic (0.3 → 0.2 → 0.1)
- [ ] Add schema validation using ajv after JSON parsing
- [ ] Implement cross-validation: verify total score matches weighted breakdown
- [ ] Add detailed logging for validation failures and retries
- [ ] Update generateAIScore() calls to use new validation function
- [ ] Preserve existing fallback logic for all-retries-failed case

## Testing Tasks

- [ ] Create unit tests for schema validation with valid responses
- [ ] Create unit tests for schema validation with invalid responses
- [ ] Test retry logic with mocked invalid then valid responses
- [ ] Test temperature decay behavior across retries
- [ ] Test cross-validation with mismatched scores
- [ ] Test fallback path when all retries exhausted
- [ ] Run benchmark with sample data from .evals/input/*.json
- [ ] Measure retry rate and schema compliance rate

## Validation Tasks

- [ ] Verify backward compatibility: response format unchanged
- [ ] Verify signature format unchanged (only score, address, timestamp signed)
- [ ] Verify latency P95 stays under 10s
- [ ] Verify schema compliance rate >95%
- [ ] Verify retry rate <5%
- [ ] Check bundle size increase acceptable (~125KB for ajv)

## Documentation Tasks

- [ ] Document schema structure in code comments
- [ ] Add logging for monitoring: retry count, validation failures
- [ ] Update oracle/CLAUDE.md with validation behavior
