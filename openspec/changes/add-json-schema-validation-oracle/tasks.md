# Tasks: Add JSON Schema Validation and Retry Logic to Oracle

## Implementation Tasks

- [x] Add ajv dependency to package.json
- [x] Define AI_RESPONSE_SCHEMA constant in oracle/app/src/index.js
- [x] Create generateAIScoreWithValidation() function with retry loop
- [x] Implement temperature decay logic (0.3 → 0.2 → 0.1)
- [x] Add schema validation using ajv after JSON parsing
- [x] Implement cross-validation: verify total score matches weighted breakdown
- [x] Add detailed logging for validation failures and retries
- [x] Update generateAIScore() calls to use new validation function
- [x] Preserve existing fallback logic for all-retries-failed case

## Testing Tasks

- [x] Create unit tests for schema validation with valid responses
- [x] Create unit tests for schema validation with invalid responses
- [x] Test retry logic with mocked invalid then valid responses
- [x] Test temperature decay behavior across retries
- [x] Test cross-validation with mismatched scores
- [x] Test fallback path when all retries exhausted
- [ ] Run benchmark with sample data from .evals/input/*.json
- [ ] Measure retry rate and schema compliance rate

## Validation Tasks

- [x] Verify backward compatibility: response format unchanged
- [x] Verify signature format unchanged (only score, address, timestamp signed)
- [ ] Verify latency P95 stays under 10s
- [ ] Verify schema compliance rate >95%
- [ ] Verify retry rate <5%
- [x] Check bundle size increase acceptable (~125KB for ajv)

## Documentation Tasks

- [x] Document schema structure in code comments
- [x] Add logging for monitoring: retry count, validation failures
- [x] Update oracle/CLAUDE.md with validation behavior
