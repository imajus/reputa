# Capability: Frontend Score Display

## Overview

The frontend score display capability presents reputation scores and breakdowns to users after analyzing their EVM wallet and questionnaire responses.

## REMOVED Requirements

### Requirement: Generate Random Score Breakdown

**Previous Behavior:**
The Analyzing page generated random scoreBreakdown values for display:
```javascript
const scoreBreakdown = {
  activity: Math.floor(Math.random() * 40) + 60,
  maturity: Math.floor(Math.random() * 40) + 60,
  diversity: Math.floor(Math.random() * 40) + 60,
  riskBehavior: Math.floor(Math.random() * 40) + 60,
  surveyMatch: Math.floor(Math.random() * 40) + 60
};
```

**Reason for Removal:**
Random scores provide no value to users and misrepresent the actual reputation analysis. With the oracle now returning real scoreBreakdown data, this placeholder logic is obsolete.

#### Scenario: No longer generate random scores

**Given** the user completes the questionnaire
**And** the oracle API returns a score with metadata.scoreBreakdown
**When** the Analyzing page processes the API response
**Then** random score generation does not occur
**And** scoreBreakdown is extracted from `response.metadata.scoreBreakdown`

---

## MODIFIED Requirements

### Requirement: Parse Score Breakdown from API Response

The frontend SHALL extract scoreBreakdown from the oracle API response metadata and use it for display in the ScoreReview page.

**Previous Behavior:**
The frontend ignored the API response metadata and generated random scores locally.

**New Behavior:**
The frontend parses `metadata.scoreBreakdown` from the API response, with fallback defaults if the field is missing.

#### Scenario: Extract breakdown from API response

**Given** the oracle API returns:
```json
{
  "score": 750,
  "wallet_address": "0x...",
  "timestamp_ms": 1738742400000,
  "signature": "0x...",
  "metadata": {
    "scoreBreakdown": {
      "activity": 85,
      "maturity": 78,
      "diversity": 62,
      "riskBehavior": 88,
      "surveyMatch": 72
    },
    "reasoning": "...",
    "risk_factors": [...],
    "strengths": [...]
  }
}
```

**When** the `fetchScore()` function processes the response
**Then** scoreBreakdown is extracted as:
```javascript
const scoreBreakdown = response.metadata?.scoreBreakdown || {
  activity: 50,
  maturity: 50,
  diversity: 50,
  riskBehavior: 50,
  surveyMatch: 50
};
```

**And** the scoreBreakdown is passed to `updateScore(response.score, scoreBreakdown)`
**And** the user navigates to /score page

#### Scenario: Handle missing scoreBreakdown gracefully

**Given** the oracle API returns a response without metadata.scoreBreakdown
**When** the `fetchScore()` function processes the response
**Then** scoreBreakdown defaults to:
```json
{
  "activity": 50,
  "maturity": 50,
  "diversity": 50,
  "riskBehavior": 50,
  "surveyMatch": 50
}
```

**And** no errors are thrown
**And** the user sees neutral scores (50) for all dimensions

---

## ADDED Requirements

### Requirement: Display Real Score Breakdown

The ScoreReview page SHALL display the scoreBreakdown values received from the oracle, showing users how their reputation score was calculated across multiple dimensions.

#### Scenario: Display non-random breakdown scores

**Given** the user has completed the questionnaire
**And** the oracle has generated scoreBreakdown: `{activity: 85, maturity: 78, diversity: 62, riskBehavior: 88, surveyMatch: 72}`
**When** the user views the ScoreReview page
**Then** the page displays:
- Activity Score: 85/100 with progress bar at 85%
- Maturity Score: 78/100 with progress bar at 78%
- Diversity Score: 62/100 with progress bar at 62%
- Risk Behavior: 88/100 with progress bar at 88%
- Survey Match: 72/100 with progress bar at 72%

**And** the scores are NOT random (repeating the flow yields same scores for same inputs)
**And** the scores reflect actual analysis of wallet and questionnaire

---

### Requirement: Update TypeScript Interface for API Response

The frontend API client SHALL define the complete response structure including the optional metadata field with scoreBreakdown.

#### Scenario: TypeScript interface includes metadata

**Given** the `ScoreResponse` interface in `lib/api.ts`
**When** the interface is defined
**Then** it includes:
```typescript
export interface ScoreResponse {
  score: number;
  wallet_address: string;
  timestamp_ms: number;
  signature: string;
  metadata?: {
    reasoning?: string;
    risk_factors?: string[];
    strengths?: string[];
    scoreBreakdown?: {
      activity: number;
      maturity: number;
      diversity: number;
      riskBehavior: number;
      surveyMatch: number;
    };
    features?: any;
  };
}
```

**And** the metadata field is optional (backward compatible)
**And** TypeScript compilation succeeds

---

### Requirement: Log AI Metadata for Debugging

The frontend SHALL optionally log AI reasoning, risk factors, and strengths from the API response to help developers understand score calculations.

#### Scenario: Log metadata when available

**Given** the oracle API returns metadata with reasoning, risk_factors, and strengths
**When** the `fetchScore()` function processes the response
**Then** the console logs:
```
Oracle response: {score: 750, metadata: {...}}
Score reasoning: Account shows strong engagement...
Risk factors: ["High token concentration"]
Strengths: ["Consistent repayment history", "High protocol diversity"]
```

**And** logging does not prevent score display
**And** missing metadata fields do not cause errors

#### Scenario: Handle missing metadata gracefully

**Given** the oracle API returns a response without optional metadata fields
**When** the `fetchScore()` function processes the response
**Then** no errors are thrown
**And** console logging is skipped for missing fields
**And** scoreBreakdown defaults are used
