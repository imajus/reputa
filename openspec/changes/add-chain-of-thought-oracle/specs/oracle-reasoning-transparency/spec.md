# Spec: Oracle Reasoning Transparency

## ADDED Requirements

### Requirement: Step-by-Step Dimension Scoring

The oracle MUST request explicit reasoning for each scoring dimension before final scores.

#### Scenario: Prompt requests step-by-step reasoning

**Given** the chain-of-thought prompt
**When** instructing the AI
**Then** the prompt MUST explicitly request for each dimension:
- Factors to consider (what data to analyze)
- Reasoning process (how to evaluate those factors)
- Score assignment (0-100 value with justification)

#### Scenario: All 5 dimensions covered

**Given** chain-of-thought output
**When** validating intermediate reasoning
**Then** intermediate_reasoning array MUST contain exactly 5 items:
- Transaction Activity
- Account Maturity
- Protocol & Token Diversity
- Risk Behavior / Financial Health
- Questionnaire Coherence

#### Scenario: Each reasoning step includes key fields

**Given** an intermediate reasoning item
**When** validating structure
**Then** it MUST include:
- `dimension` (string): Name of the dimension
- `factors_considered` (string, optional): What data was analyzed
- `reasoning` (string): Explanation of scoring logic
- `score` (integer, 0-100): Assigned score for this dimension

---

### Requirement: Self-Verification

The oracle MUST request AI to verify its own work for consistency.

#### Scenario: Formula verification step

**Given** the chain-of-thought prompt
**When** instructing final verification
**Then** the prompt MUST ask AI to:
- Calculate total score using weighted formula
- Compare calculated total to stated total score
- Flag any discrepancies

#### Scenario: Verification result in output

**Given** chain-of-thought response
**When** parsing the output
**Then** it MUST include `verification_passed` boolean field

#### Scenario: Verification failure triggers retry

**Given** a response with verification_passed: false
**When** validating the response
**Then** the system MUST treat it as validation failure and retry (if retries remaining)

---

### Requirement: Extended JSON Schema for Chain-of-Thought

The chain-of-thought scoring MUST use an extended JSON schema including intermediate reasoning.

#### Scenario: Schema includes intermediate_reasoning

**Given** the CoT JSON schema
**When** validating responses
**Then** the schema MUST require:
- `intermediate_reasoning` array with 5 items
- Each item with dimension, reasoning, score fields

#### Scenario: Schema includes verification_passed

**Given** the CoT JSON schema
**When** validating responses
**Then** the schema MUST require `verification_passed` boolean field

#### Scenario: Backward compatible metadata

**Given** a CoT response
**When** returning to client
**Then** intermediate_reasoning and verification_passed MUST be in metadata (unsigned)
**And** core signed fields (score, wallet_address, timestamp_ms) MUST remain unchanged

---

### Requirement: Shadow Mode Deployment

Chain-of-thought MUST be deployed in shadow mode before production to validate quality and performance.

#### Scenario: Dual scoring in shadow mode

**Given** shadow mode is enabled
**When** processing a scoring request
**Then** the system MUST:
- Generate standard score (return this to client)
- Generate CoT score (log for analysis)
- Compare results in logs

#### Scenario: Shadow mode logging

**Given** shadow mode is active
**When** CoT scoring completes
**Then** the system MUST log:
- Full CoT response including intermediate_reasoning
- Comparison to standard response (score delta)
- Latency for CoT vs standard

#### Scenario: No impact on production

**Given** shadow mode is enabled
**When** serving client requests
**Then** only standard scores MUST be returned
**And** CoT latency MUST not affect response time

---

### Requirement: Token Budget Management

Chain-of-thought MUST operate within extended token budget constraints.

#### Scenario: Increased num_predict

**Given** chain-of-thought enabled
**When** calling Ollama API
**Then** num_predict MUST be increased to at least 1200 tokens (from 800)

#### Scenario: Monitor token usage

**Given** CoT responses
**When** generating scores
**Then** the system MUST log actual token usage per request

#### Scenario: Handle truncation

**Given** a response that exceeds token limit
**When** parsing the truncated output
**Then** the system MUST:
- Detect truncation via incomplete JSON
- Log the truncation event
- Retry with standard prompt (fallback)

---

### Requirement: Performance Constraints

Chain-of-thought MUST meet acceptable latency targets.

#### Scenario: Latency under 15s

**Given** CoT scoring enabled in production
**When** measuring P95 latency
**Then** latency MUST be ≤15 seconds

#### Scenario: Shadow mode latency tracking

**Given** shadow mode evaluation
**When** comparing CoT vs standard
**Then** latency increase MUST be measured and logged

#### Scenario: Quality justifies latency

**Given** shadow mode results
**When** deciding to promote to production
**Then** CoT MUST show >10% improvement in consistency or accuracy to justify +2-4s latency

---

### Requirement: Hybrid Approach Option

If full CoT proves too slow, the oracle MUST support CoT for edge cases only.

#### Scenario: Selective CoT trigger

**Given** hybrid mode enabled
**When** standard scoring succeeds without issues
**Then** CoT MUST NOT be used (return standard result)

#### Scenario: CoT for validation failures

**Given** hybrid mode enabled
**When** standard scoring fails validation
**Then** CoT MUST be triggered as retry mechanism

#### Scenario: Optional API parameter

**Given** a client request
**When** the request includes `?cot=true` parameter
**Then** CoT scoring MUST be used regardless of mode

---

### Requirement: Quality Metrics

Chain-of-thought deployment MUST be data-driven based on measurable improvements.

#### Scenario: Consistency measurement

**Given** shadow mode data
**When** evaluating CoT quality
**Then** standard deviation of scores for same wallet MUST be calculated for both methods

#### Scenario: Self-verification rate

**Given** CoT responses
**When** analyzing quality
**Then** verification_passed rate MUST be tracked (target: >95%)

#### Scenario: Reasoning quality assessment

**Given** 20 sample CoT responses
**When** manually reviewing
**Then** reasoning MUST be evaluated for:
- Logical consistency
- Relevance to stated factors
- Alignment with final scores
