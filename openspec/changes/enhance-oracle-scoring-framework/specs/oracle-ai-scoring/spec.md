# Capability: Oracle AI Scoring

## Overview

The oracle AI scoring capability analyzes EVM wallet data and user questionnaire responses to generate reputation scores for DeFi lending protocols. It leverages Ollama LLM for sophisticated multi-factor analysis.

## MODIFIED Requirements

### Requirement: Parse Rich EVM Data Structure

The oracle SHALL parse the enhanced EVM data structure from the n8n webhook endpoint, extracting pre-calculated wallet metadata, DeFi protocol interactions, lending history, token portfolio metrics, and NFT ownership.

**Previous Behavior:**
The oracle parsed `EVM.Events[]` array containing block timestamps, contract addresses, and transaction values. Feature extraction manually calculated account age, detected protocols by address prefix, and counted transactions.

**New Behavior:**
The oracle parses the new data structure with pre-calculated metrics:
- `wallet_metadata`: account age, transaction counts, unique counterparties, average monthly activity
- `defi_analysis.protocol_interactions`: detected protocols (Aave, Compound, Uniswap, Curve, Morpho), interaction counts
- `lending_history.protocol_analysis.protocols`: borrow/repay/liquidate/supply/withdraw event counts per protocol
- `tokens.holdings`: token balances, USD values, categories
- `tokens.concentration`: Herfindahl index, diversification score, concentration metrics
- `nfts.poaps` and `nfts.legit_nfts`: POAP and NFT ownership
- `eth_balance`: ETH balance

#### Scenario: Extract features from new EVM data format

**Given** the n8n endpoint returns:
```json
{
  "wallet": "0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A",
  "wallet_metadata": {
    "wallet_age_days": 1262,
    "total_transactions": 2681,
    "unique_counterparties": 315,
    "average_txs_per_month": 63.73
  },
  "defi_analysis": {
    "protocol_interactions": {
      "curve": true,
      "morpho": true,
      "total_protocols": 2
    }
  },
  "lending_history": {
    "protocol_analysis": {
      "protocols": {
        "0xbbbb...": {
          "borrow_count": 5,
          "repay_count": 5,
          "liquidate_count": 0
        }
      }
    }
  },
  "tokens": {
    "concentration": {
      "diversification_score": 45,
      "herfindahl_index": 0.8,
      "num_tokens": 49
    }
  }
}
```

**When** `extractWalletFeatures(evmData)` is called
**Then** the function returns:
```json
{
  "walletAge": 1262,
  "totalTransactions": 2681,
  "avgTxsPerMonth": 63.73,
  "uniqueCounterparties": 315,
  "protocolsUsed": 2,
  "protocolNames": ["curve", "morpho"],
  "borrowCount": 5,
  "repayCount": 5,
  "liquidateCount": 0,
  "numTokens": 49,
  "diversificationScore": 45,
  "concentrationRisk": 0.8
}
```

**And** no errors are raised
**And** old logic (timestamp parsing, protocol detection by address) is removed

---

### Requirement: Incorporate Questionnaire into AI Scoring

The AI scoring function SHALL accept user questionnaire responses and incorporate them into the reputation analysis, specifically influencing creditworthiness and intent alignment scores.

#### Scenario: Score with questionnaire responses

**Given** wallet features extracted from EVM data
**And** a questionnaire array:
```json
[
  {"question": "Who controls this wallet?", "answer": "individual"},
  {"question": "What is the loan for?", "answer": "working capital"},
  {"question": "Off-chain revenue streams?", "answer": "e-commerce business with $50k monthly revenue"}
]
```

**When** `generateAIScore(features, questionnaire)` is called
**Then** the AI prompt includes:
- Section 1: On-Chain Activity (wallet metadata, DeFi protocols, lending history, tokens, NFTs)
- Section 2: Borrower Profile (formatted questionnaire Q&A)
- Section 3: Scoring Instructions with 5 dimensions

**And** the AI analyzes coherence between stated intent and on-chain behavior
**And** creditworthiness score reflects revenue disclosure and liability transparency
**And** intent alignment score measures consistency between questionnaire and transactions

#### Scenario: Score without questionnaire (backward compatibility)

**Given** wallet features extracted from EVM data
**And** questionnaire is empty array or null

**When** `generateAIScore(features, questionnaire)` is called
**Then** the AI prompt includes "No questionnaire data provided." in Borrower Profile section
**And** scoring proceeds based on EVM data only
**And** surveyMatch (intent alignment) score defaults to 50 (neutral)
**And** no errors are raised

---

## ADDED Requirements

### Requirement: Return Detailed Score Breakdown

The AI scoring function SHALL return a breakdown of the total score across 5 dimensions: transaction activity, account maturity, protocol & token diversity, risk behavior / financial health, and questionnaire coherence.

#### Scenario: AI returns score with breakdown

**Given** the AI successfully analyzes wallet features and questionnaire
**When** `generateAIScore(features, questionnaire)` is called
**Then** the return value includes:
```json
{
  "score": 750,
  "scoreBreakdown": {
    "activity": 85,
    "maturity": 78,
    "diversity": 62,
    "riskBehavior": 88,
    "surveyMatch": 72
  },
  "reasoning": "Account shows strong engagement...",
  "risk_factors": ["High token concentration"],
  "strengths": ["Consistent repayment history", "High protocol diversity"]
}
```

**And** all breakdown values are integers between 0 and 100
**And** breakdown fields match frontend expectations exactly

#### Scenario: Fallback score breakdown when AI unavailable

**Given** Ollama service is unavailable
**And** wallet features have been extracted

**When** `generateAIScore(features, questionnaire)` falls back to simple scoring
**Then** total score is calculated as `min(1000, totalTransactions * 10)`
**And** scoreBreakdown is generated proportionally:
```json
{
  "activity": Math.round(totalScore * 0.20 / 10),
  "maturity": Math.round(totalScore * 0.20 / 10),
  "diversity": Math.round(totalScore * 0.20 / 10),
  "riskBehavior": Math.round(totalScore * 0.25 / 10),
  "surveyMatch": 50
}
```

**And** all values are clamped to 0-100 range
**And** reasoning indicates "Fallback scoring: AI unavailable"

---

### Requirement: Format Questionnaire for AI Readability

The oracle SHALL format questionnaire responses into a human-readable format suitable for LLM analysis.

#### Scenario: Format questionnaire with multiple questions

**Given** a questionnaire array:
```json
[
  {"question": "Who controls this wallet?", "answer": "individual"},
  {"question": "Loan purpose?", "answer": "working capital"}
]
```

**When** `formatQuestionnaireForAI(questionnaire)` is called
**Then** the function returns:
```
Q1: Who controls this wallet?
A1: individual

Q2: Loan purpose?
A2: working capital
```

#### Scenario: Handle empty questionnaire

**Given** questionnaire is null, undefined, or empty array
**When** `formatQuestionnaireForAI(questionnaire)` is called
**Then** the function returns "No questionnaire data provided."
**And** no errors are raised

#### Scenario: Handle missing answers

**Given** a questionnaire with unanswered questions:
```json
[
  {"question": "Who controls this wallet?", "answer": "individual"},
  {"question": "Loan purpose?", "answer": ""}
]
```

**When** `formatQuestionnaireForAI(questionnaire)` is called
**Then** the function returns:
```
Q1: Who controls this wallet?
A1: individual

Q2: Loan purpose?
A2: (not answered)
```

---

### Requirement: Validate Score Breakdown

The oracle SHALL validate scoreBreakdown objects from AI responses, providing defaults when fields are missing or invalid.

#### Scenario: Validate complete breakdown

**Given** AI returns breakdown:
```json
{
  "activity": 85,
  "maturity": 78,
  "diversity": 62,
  "riskBehavior": 88,
  "surveyMatch": 72
}
```

**When** `validateScoreBreakdown(breakdown)` is called
**Then** the function returns the breakdown unchanged
**And** all values remain integers between 0-100

#### Scenario: Clamp out-of-range values

**Given** AI returns breakdown with invalid values:
```json
{
  "activity": 150,
  "maturity": -20,
  "diversity": 62,
  "riskBehavior": 88,
  "surveyMatch": 72
}
```

**When** `validateScoreBreakdown(breakdown)` is called
**Then** the function returns:
```json
{
  "activity": 100,
  "maturity": 0,
  "diversity": 62,
  "riskBehavior": 88,
  "surveyMatch": 72
}
```

#### Scenario: Provide defaults for missing breakdown

**Given** AI returns null or invalid breakdown object
**When** `validateScoreBreakdown(breakdown)` is called
**Then** the function returns:
```json
{
  "activity": 50,
  "maturity": 50,
  "diversity": 50,
  "riskBehavior": 50,
  "surveyMatch": 50
}
```

---

### Requirement: Include Breakdown in API Response

The POST /score endpoint SHALL include scoreBreakdown in the response metadata while maintaining backward compatibility with signature format.

#### Scenario: API response includes breakdown

**Given** a POST request to /score with valid address and questionnaire
**When** the oracle processes the request successfully
**Then** the response includes:
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

**And** signature is generated from `{score, wallet_address, timestamp_ms}` only
**And** metadata is NOT included in signature
**And** signature validates on-chain with Move contract (unchanged)

#### Scenario: GET endpoint backward compatibility

**Given** a GET request to /score?address=0x...
**When** the oracle processes the request (no questionnaire)
**Then** the response includes scoreBreakdown with surveyMatch defaulting to 50
**And** all other scoring proceeds normally
**And** no errors are raised
