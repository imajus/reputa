# Spec: Oracle Few-Shot Examples

## ADDED Requirements

### Requirement: Few-Shot Example Structure

The oracle prompt MUST include 2-3 example wallet analyses demonstrating correct scoring behavior.

#### Scenario: Examples cover score distribution

**Given** the few-shot examples
**When** reviewing the examples
**Then** they MUST cover three score ranges:
- High reputation: 800-900
- Medium reputation: 400-600
- Low reputation: 100-300

#### Scenario: Examples demonstrate all dimensions

**Given** each example
**When** showing the scoreBreakdown
**Then** it MUST include non-zero values for all 5 dimensions:
- activity
- maturity
- diversity
- riskBehavior
- surveyMatch

#### Scenario: Examples show input features

**Given** each example
**When** displaying the input
**Then** it MUST include representative values for:
- Wallet age (days)
- Transaction counts
- Protocol usage
- Lending history (borrow/repay/liquidate counts)
- Token portfolio metrics
- Questionnaire responses

---

### Requirement: Example Integration in Prompt

The examples MUST be positioned correctly in the prompt structure.

#### Scenario: Examples after instructions

**Given** the AI prompt structure
**When** constructing the prompt
**Then** examples MUST appear:
- After scoring instructions and schema
- Before the actual wallet data to analyze

#### Scenario: Clear separation markers

**Given** the prompt with examples
**When** AI reads the prompt
**Then** examples MUST be clearly separated from actual task using section headers:
- "## Example 1: High-Reputation Wallet"
- "## Example 2: Medium-Reputation Wallet"
- "## Example 3: Low-Reputation Wallet"
- "## Your Task"

---

### Requirement: Example Accuracy and Consistency

The examples MUST be factually correct and follow documented scoring rules.

#### Scenario: Scores match formula

**Given** each example's scoreBreakdown
**When** calculating expected total score
**Then** the total score MUST match the weighted formula within 2%:
```
(activity × 2 + maturity × 2 + diversity × 2 + riskBehavior × 2.5 + surveyMatch × 1.5) / 10
```

#### Scenario: Reasoning aligns with scores

**Given** each example's reasoning field
**When** reviewing the text
**Then** it MUST explicitly mention factors justifying the scores

#### Scenario: Risk factors and strengths match profile

**Given** each example's risk_factors and strengths arrays
**When** comparing to input features
**Then** they MUST be consistent with the wallet profile (e.g., high liquidations → risk factor)

---

### Requirement: Token Budget Compliance

The few-shot examples MUST fit within the token budget.

#### Scenario: Examples under 400 tokens

**Given** all three examples combined
**When** counting tokens
**Then** total MUST be ≤400 tokens

#### Scenario: Total prompt under limit

**Given** instructions + examples + actual wallet data
**When** constructing full prompt
**Then** total MUST fit within num_predict: 800 budget with headroom for response
