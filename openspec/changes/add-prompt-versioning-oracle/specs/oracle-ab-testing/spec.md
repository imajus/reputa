# Spec: Oracle A/B Testing

## ADDED Requirements

### Requirement: Evaluation Framework

The oracle MUST provide tooling to scientifically compare prompt versions before deployment.

#### Scenario: Load evaluation samples

**Given** sample wallet data in .evals/input/*.json
**When** running evaluation script
**Then** all sample files MUST be loaded and parsed

#### Scenario: Run multiple iterations per sample

**Given** a prompt version to evaluate
**When** scoring each sample
**Then** the sample MUST be scored 10 times to measure consistency

#### Scenario: Calculate consistency metrics

**Given** 10 scoring runs for a sample
**When** calculating metrics
**Then** the script MUST compute:
- Mean score
- Standard deviation
- Min and max scores

#### Scenario: Compare two prompt versions

**Given** results from two prompt versions
**When** generating comparison report
**Then** the report MUST show:
- Consistency improvement (% change in avg std dev)
- Score distribution differences
- Schema compliance rate for each version

---

### Requirement: Gradual Rollout (A/B Testing)

The oracle MUST support gradual rollout of new prompts to a percentage of traffic.

#### Scenario: Deterministic prompt selection

**Given** a wallet address
**When** selecting which prompt to use
**Then** the selection MUST be deterministic based on the address

#### Scenario: Configurable rollout percentage

**Given** a new prompt version
**When** configuring A/B testing
**Then** rollout percentage MUST be adjustable (e.g., 10%, 25%, 50%)

#### Scenario: Fair distribution

**Given** a rollout percentage of 10%
**When** selecting prompts for random wallets
**Then** approximately 10% MUST receive the new prompt

#### Scenario: Use address for split

**Given** a wallet address
**When** determining A/B split
**Then** the last byte of the address MUST be used for distribution:
```
if (parseInt(address.slice(-2), 16) < (256 * rolloutPct / 100)) {
  use new prompt
} else {
  use stable prompt
}
```

---

### Requirement: Monitoring and Logging

The oracle MUST log prompt version usage for monitoring and debugging.

#### Scenario: Log prompt version per request

**Given** a scoring request
**When** processing the request
**Then** the log MUST include which prompt version was used

#### Scenario: Log A/B split decisions

**Given** A/B testing is active
**When** a prompt is selected
**Then** the log MUST record:
- Wallet address (for debugging)
- Selected prompt version
- Rollout percentage at time of request

---

### Requirement: Evaluation Metrics

Prompt evaluation MUST measure key quality indicators.

#### Scenario: Measure consistency

**Given** evaluation results
**When** comparing prompts
**Then** average standard deviation MUST be calculated across all samples

#### Scenario: Measure schema compliance

**Given** evaluation results
**When** comparing prompts
**Then** schema compliance rate (% valid outputs) MUST be calculated

#### Scenario: Detect regressions

**Given** a new prompt version evaluation
**When** comparing to baseline
**Then** the script MUST flag if:
- Consistency degrades (avg std dev increases)
- Schema compliance drops
- Score distribution becomes abnormal (clustering, drift)
