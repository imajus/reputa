# Reputa Scoring Framework

AI-powered DeFi reputation scoring system analyzing Ethereum wallet activity and borrower intent using Ollama LLM and on-chain data aggregation.

## Overview

Reputa generates creditworthiness scores (0-1000) by combining on-chain behavioral analytics from Ethereum with user-provided questionnaire responses. The scoring engine runs inside a Trusted Execution Environment (TEE) to ensure integrity, signs scores cryptographically, and records them on Sui blockchain for protocol integration.

**Scoring Range:** 0-1000 points
- **800-1000**: Premium Tier - Exceptional DeFi track record
- **600-799**: Standard Tier - Solid engagement and financial health
- **0-599**: Basic Tier - Emerging or limited activity

## Score Components

The total score is calculated as a weighted average of five dimensions, each scored 0-100:

```
Total Score = (Activity × 2.0) + (Maturity × 2.0) + (Diversity × 2.0) + (Risk Behavior × 2.5) + (Intent Alignment × 1.5)
Maximum = 1000 points
```

### 1. Transaction Activity (Weight: 2.0, Max: 200 points)

Measures wallet engagement frequency, transaction volume, and recent activity patterns.

**Analyzed Metrics:**
- Total transaction count (lifetime)
- Average transactions per month
- Transaction frequency trends
- Recent engagement (last 30/90 days)

**Scoring Logic:**
- Higher transaction counts indicate established usage
- Consistent monthly activity shows reliability
- Recent transactions demonstrate active wallet management
- Gaps in activity may reduce score

**Data Source:** `wallet_metadata.total_transactions`, `wallet_metadata.average_txs_per_month`

### 2. Account Maturity (Weight: 2.0, Max: 200 points)

Evaluates account age and usage consistency over time.

**Analyzed Metrics:**
- Wallet age in days
- Usage consistency across months
- Account lifecycle patterns

**Scoring Logic:**
- Older wallets (1+ years) score higher
- Consistent activity over time shows stability
- Brand new wallets receive lower baseline scores
- Long dormant periods reduce maturity scores

**Data Source:** `wallet_metadata.wallet_age_days`

### 3. Protocol & Token Diversity (Weight: 2.0, Max: 200 points)

Assesses DeFi sophistication through protocol interactions, token holdings, and counterparty diversity.

**Analyzed Metrics:**
- Number of DeFi protocols used (Aave, Compound, Curve, Morpho, etc.)
- Token portfolio size and diversification score
- Unique counterparties interacted with
- Concentration risk (Herfindahl Index)
- NFT holdings and POAPs

**Scoring Logic:**
- Multiple protocol usage (3+) indicates DeFi experience
- Well-diversified token portfolios score higher
- High concentration risk (Herfindahl > 0.7) reduces score
- NFT holdings and POAPs show ecosystem participation
- More unique counterparties demonstrate network effects

**Data Sources:**
- `defi_analysis.protocol_interactions.total_protocols`
- `tokens.concentration.diversification_score`
- `tokens.concentration.herfindahl_index`
- `wallet_metadata.unique_counterparties`
- `nfts.poaps`, `nfts.legit_nfts`

### 4. Risk Behavior / Financial Health (Weight: 2.5, Max: 250 points)

Evaluates lending behavior, liquidation history, and financial risk management.

**Analyzed Metrics:**
- Borrow vs repay event ratio
- Liquidation history
- Token concentration risk
- Lending protocol performance
- Liability disclosure from questionnaire

**Scoring Logic:**
- Clean repayment history (repay_count ≥ borrow_count) scores highest
- Zero liquidations is ideal
- Any liquidation events significantly reduce score
- High concentration risk penalizes this dimension
- Transparent liability disclosure in questionnaire improves score

**Data Sources:**
- `lending_history.protocol_analysis.protocols[].borrow_count`
- `lending_history.protocol_analysis.protocols[].repay_count`
- `lending_history.protocol_analysis.protocols[].liquidate_count`
- `tokens.concentration.herfindahl_index`

**Red Flags:**
- Outstanding loans (borrow_count > repay_count)
- Liquidation events
- Undisclosed liabilities in questionnaire
- Excessive leverage indicators

### 5. Intent Alignment / Questionnaire Coherence (Weight: 1.5, Max: 150 points)

Measures alignment between stated borrowing intent and actual on-chain behavior.

**Analyzed Factors:**
- Wallet controller type (individual, organization, shared treasury)
- Stated loan purpose vs transaction patterns
- Risk tolerance vs actual leverage behavior
- Collateral preferences vs holdings
- Consistency across questionnaire responses

**Scoring Logic:**
- Strong coherence between answers and on-chain data scores highest
- Contradictions reduce score (e.g., claims conservative but high leverage)
- If no questionnaire provided, defaults to 50 (neutral)
- Transparent responses about existing liabilities improve score

**Data Source:** User questionnaire responses analyzed against all on-chain metrics

## Data Sources & Aggregation

### Primary Data Pipeline

```
EVM Wallet Address → POST https://reputa-data.majus.app/aggregate
                                    ↓
                        Rich analytics payload returned
                                    ↓
                        oracle/app/src/index.js (extractWalletFeatures)
                                    ↓
                        Ollama AI scoring (llama3.2:1b)
                                    ↓
                        Score + 5-dimension breakdown
```

### Aggregate API Response Structure

```json
{
  "wallet": "0x...",
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
        "0xProtocolAddress": {
          "borrow_count": 5,
          "repay_count": 5,
          "liquidate_count": 0,
          "supply_count": 12,
          "withdraw_count": 10
        }
      }
    }
  },
  "tokens": {
    "concentration": {
      "diversification_score": 45,
      "herfindahl_index": 0.8,
      "num_tokens": 49
    },
    "holdings": [...]
  },
  "nfts": {
    "poaps": [...],
    "legit_nfts": [...]
  },
  "eth_balance": 0.082
}
```

### Tracked DeFi Protocols

**Lending/Borrowing:**
- Aave V2 & V3
- Compound V2 & V3
- Morpho

**DEX:**
- Uniswap V2 & V3
- Curve Finance

**Data Provider:** Aggregate API consolidates data from Alchemy API and Etherscan API

## AI Scoring Engine

### Implementation

Reputa uses Ollama (llama3.2:1b model) for intelligent scoring analysis. The AI receives structured prompts containing:
- Complete on-chain feature set (15+ metrics)
- Formatted questionnaire responses
- Scoring instructions with dimension definitions

**Configuration:**
- Model: `llama3.2:1b`
- Temperature: 0.3 (low variance for consistency)
- Max tokens: 800
- Output format: JSON

### Prompt Structure

The AI receives:
1. **On-Chain Activity Section**: Formatted wallet metadata, DeFi interactions, lending history, token portfolio, NFTs
2. **Borrower Profile Section**: Formatted questionnaire Q&A pairs
3. **Scoring Instructions**: Explicit dimension definitions, weight formulas, output format requirements

### AI Output Format

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
  "reasoning": "Account shows strong engagement with consistent repayment behavior...",
  "risk_factors": ["High token concentration"],
  "strengths": ["Consistent repayment history", "Multiple protocol usage"]
}
```

### Fallback Mechanism

If AI scoring fails (Ollama unavailable), the system falls back to simple transaction-based scoring:
```
Fallback Score = min(1000, total_transactions × 10)
Breakdown = uniform distribution across 5 dimensions
```

## Response Format

### Signed Score Response (from Oracle API)

```json
{
  "score": 750,
  "wallet_address": "0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba",
  "timestamp_ms": 1738742400000,
  "signature": "0x3045022100...",
  "metadata": {
    "scoreBreakdown": {
      "activity": 85,
      "maturity": 78,
      "diversity": 62,
      "riskBehavior": 88,
      "surveyMatch": 72
    },
    "reasoning": "Account shows strong engagement...",
    "risk_factors": ["High token concentration"],
    "strengths": ["Consistent repayment history"],
    "features": {
      "walletAge": 1262,
      "totalTransactions": 2681,
      "protocolsUsed": 3,
      ...
    }
  }
}
```

**Critical Note:**
- `score`, `wallet_address`, `timestamp_ms` are **signed** by TEE enclave and verified on-chain
- `metadata` (including scoreBreakdown) is **unsigned** and for display purposes only
- Only the signed values are stored on Sui blockchain

## Frontend Display

The score review page (`frontend/src/pages/ScoreReview.tsx`) displays:

1. **Total Score Gauge**: Semi-circle visualization showing score/1000
2. **Tier Badge**: Premium/Standard/Basic based on score range
3. **5-Dimension Breakdown**: Progress bars for each component (0-100)
   - Transaction Activity (TrendingUp icon)
   - Account Maturity (Award icon)
   - Protocol & Token Diversity (Layers icon)
   - Financial Health (Shield icon)
   - Intent Alignment (Target icon)

## Scoring Philosophy

### What We Reward

- **Consistent engagement**: Regular transactions over time
- **Established history**: Older wallets with proven track records
- **DeFi sophistication**: Multiple protocol usage and diverse holdings
- **Financial responsibility**: Clean repayment history, no liquidations
- **Transparency**: Honest questionnaire responses aligned with on-chain data

### What We Penalize

- **Liquidation events**: Strong negative signal of risk management failure
- **Outstanding loans**: Unpaid borrowings without repayment events
- **High concentration risk**: Over-reliance on single assets
- **Misaligned intent**: Contradictions between stated purpose and behavior
- **Undisclosed liabilities**: Failure to disclose existing debts in questionnaire

### What We Don't Track (Yet)

- **Gas spending analysis**: Could indicate commitment but not yet implemented
- **DAO governance participation**: Potential reputation signal
- **Cross-chain activity**: Only Ethereum mainnet currently analyzed
- **Social reputation**: No integration with Lens, Farcaster, etc.
- **Identity verification**: No KYC or sybil detection

## Technical Architecture

### Signature Verification

The oracle signs scores using secp256k1 inside a TEE enclave. The signature covers:

```move
public struct ScoreUpdatePayload has copy, drop {
    score: u64,
    wallet_address: String,
}

public struct IntentMessage<T: copy + drop> has copy, drop {
    intent: u8,
    timestamp_ms: u64,
    data: T,
}
```

**Verification on Sui:**
1. Reconstruct `IntentMessage<ScoreUpdatePayload>` from transaction parameters
2. Serialize using BCS (Binary Canonical Serialization)
3. Hash with SHA256
4. Verify signature using enclave's registered public key
5. Store score if valid, abort transaction if invalid

### On-Chain Storage

```move
public struct WalletScore has key, store {
    id: UID,
    score: u64,                // 0-1000
    wallet_address: String,    // EVM address (e.g., "0x...")
    timestamp_ms: u64,
    version: u64,              // Increments on updates
}
```

Each wallet can have multiple WalletScore objects owned by different Sui addresses. Updates create new versions rather than modifying existing records.

## API Endpoints

### GET /score?address=0x...

Fetch score without questionnaire (backward compatible).

**Response:** Signed score with surveyMatch defaulting to 50.

### POST /score

Fetch score with optional questionnaire data.

**Request:**
```json
{
  "address": "0x...",
  "questionnaire": [
    {"question": "Who controls this wallet?", "answer": "individual"},
    {"question": "What is the loan for?", "answer": "working capital"}
  ]
}
```

**Response:** Same format as GET endpoint but with enhanced surveyMatch scoring.

## Limitations & Considerations

1. **Ethereum Mainnet Only**: No support for L2s, sidechains, or other L1s
2. **Limited Protocol Coverage**: Only tracks major DeFi protocols (Aave, Compound, etc.)
3. **Price Data Delays**: Token valuations may lag market prices
4. **AI Model Variance**: Ollama responses have inherent non-determinism despite low temperature
5. **No Cross-Chain View**: Cannot detect reputation on other blockchains
6. **No Sybil Detection**: Multiple wallets by same entity are scored independently
7. **Transaction History Limits**: API rate limits may restrict historical depth

## Future Enhancements

- Real-time liquidation monitoring across protocols
- Cross-chain reputation aggregation (Solana, Sui, etc.)
- Social graph integration (Lens Protocol, Farcaster)
- DAO governance participation tracking
- Gitcoin donation history
- On-chain identity verification (ENS, Proof of Humanity)
- Machine learning model training on historical default data
- Sybil attack detection using graph analysis
