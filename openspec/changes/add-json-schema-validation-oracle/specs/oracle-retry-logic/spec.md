# Spec: Oracle Retry Logic

## ADDED Requirements

### Requirement: Logging for Validation Failures

The oracle MUST log detailed information about validation failures and retry attempts for monitoring and debugging.

#### Scenario: Log schema validation failures

**Given** a schema validation failure
**When** ajv validator detects errors
**Then** the system MUST log:
- Attempt number
- Validation error details from ajv
- Current temperature value

#### Scenario: Log cross-validation failures

**Given** a score mismatch
**When** cross-validation fails
**Then** the system MUST log:
- Attempt number
- Expected score (from formula)
- Actual score (from AI)
- Delta value

---

### Requirement: Backward Compatibility

The validation system MUST maintain backward compatibility with existing API contract and signature format.

#### Scenario: Response format unchanged

**Given** a successful validation
**When** returning the response
**Then** the response format MUST match existing structure:
- `score`, `wallet_address`, `timestamp_ms`, `signature` (signed)
- `metadata` object with `scoreBreakdown`, `reasoning`, `risk_factors`, `strengths` (unsigned)

#### Scenario: Signature format unchanged

**Given** a validated score
**When** signing the data
**Then** only `score`, `wallet_address`, and `timestamp_ms` MUST be included in signature
**And** metadata MUST NOT be signed

---

### Requirement: Performance Constraints

The validation and retry system MUST operate within TEE resource constraints and latency budget.

#### Scenario: Validation overhead acceptable

**Given** a successful first-attempt response
**When** validating with ajv
**Then** overhead MUST be ≤200ms

#### Scenario: P95 latency under budget

**Given** all requests including retries
**When** measuring P95 latency
**Then** total latency MUST be ≤10 seconds

#### Scenario: Retry rate low

**Given** production traffic
**When** measuring retry frequency
**Then** retry rate MUST be <5% of requests
