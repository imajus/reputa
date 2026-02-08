# Spec: Oracle JSON Schema Validation

## ADDED Requirements

### Requirement: JSON Schema Definition for AI Responses

The oracle MUST define a formal JSON schema matching the expected AI response structure with type constraints and value ranges.

#### Scenario: Schema defines all required fields

**Given** the AI generates a response
**When** the response is parsed
**Then** it MUST be validated against a schema requiring:
- `score` (integer, 0-1000)
- `scoreBreakdown` (object with 5 integer fields, each 0-100)
- `reasoning` (string, 10-500 characters)
- `risk_factors` (array of strings)
- `strengths` (array of strings)

#### Scenario: Schema enforced at grammar level

**Given** a scoring request
**When** calling Ollama generate API
**Then** the schema MUST be passed via `format` parameter for grammar-based constraint enforcement

#### Scenario: Schema validation using ajv

**Given** a parsed AI response
**When** validating the structure
**Then** ajv validator MUST verify all required fields exist and values meet constraints

---

### Requirement: Retry Logic on Validation Failures

The oracle MUST implement retry logic when AI responses fail schema validation, with temperature decay to improve consistency.

#### Scenario: Retry up to 3 attempts

**Given** an AI response that fails schema validation
**When** the first attempt fails
**Then** the system MUST retry up to 2 more times (3 total attempts)

#### Scenario: Temperature decay across retries

**Given** multiple retry attempts
**When** retrying after validation failure
**Then** temperature MUST decrease:
- Attempt 1: 0.3
- Attempt 2: 0.2
- Attempt 3: 0.1

#### Scenario: Fallback after all retries fail

**Given** all 3 retry attempts fail validation
**When** no valid response obtained
**Then** the system MUST fall back to existing simple scoring logic

---

### Requirement: Cross-Validation of Total Score vs Breakdown

The oracle MUST verify that the AI's total score matches the weighted breakdown formula.

#### Scenario: Calculate expected score from breakdown

**Given** a scoreBreakdown object
**When** cross-validating
**Then** expected score MUST be calculated as:
```
(activity × 2 + maturity × 2 + diversity × 2 + riskBehavior × 2.5 + surveyMatch × 1.5) / 10
```

#### Scenario: Allow 2% tolerance

**Given** a calculated expected score and AI-provided total score
**When** comparing values
**Then** the difference MUST be ≤20 points (2% of 1000)

#### Scenario: Retry on score mismatch

**Given** a score mismatch exceeding 2% tolerance
**When** validation fails
**Then** the system MUST retry with next attempt (if retries remaining)
