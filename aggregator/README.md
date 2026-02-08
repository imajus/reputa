# On-Chain Data Aggregation & Credit Assessment API

A FastAPI-based service that aggregates Ethereum wallet data and provides DeFi-focused credit assessment.

## Overview

This service collects on-chain data from various sources (NFTs, tokens, transaction history, DeFi protocols) and performs comprehensive credit analysis focused on lending behavior, liquidity management, and financial health.

## Scoring Methodology

The credit score is calculated based on four primary components:

### 1. Payment History

- **Repayment timelines**: Track of borrowed vs. repaid loans
- **Punctuality score**: On-time repayment behavior
- **Protocol performance**: Average repayment rate across DeFi protocols

### 2. Leverage & Solvency

- **Liquidity buffers**: Cash reserves relative to total assets
- **Stress testing**: Resilience under market volatility scenarios
- **Treasury health**: Net asset value and composition

### 3. Use of Proceeds

- **Capital looping detection**: Identifies excessive borrow-to-deposit cycles
- **Productive capital use**: Rewards legitimate DeFi participation

### 4. Cash Flow

- **Debt Service Coverage Ratio (DSCR)**: Ability to service debt obligations
- **Stress scenarios**: Cash flow resilience under adverse conditions

### Penalty Factors

- Outstanding loans (unpaid borrowings)
- Emergency repayment patterns
- Excessive capital looping (>50% loop ratio)
- Poor portfolio diversification (high Herfindahl index)

## API Endpoints

All endpoints accept POST requests with a JSON body containing the wallet address.

### POST /assets/nfts

Fetches and classifies NFT holdings.

**Request:**
```json
{
  "wallet_address": "0x..."
}
```

**Response:** Classified NFTs with spam detection and verification status.

### POST /assets/tokens

Fetches token balances with enrichment and portfolio concentration metrics.

**Request:**
```json
{
  "wallet_address": "0x..."
}
```

**Response:**
```json
{
  "tokens": [...],
  "concentration_metrics": {
    "herfindahl_index": 0.45,
    "top_holdings_pct": 0.67
  }
}
```

### POST /history/transfers

Retrieves incoming and outgoing asset transfers.

**Request:**
```json
{
  "wallet_address": "0x..."
}
```

**Response:**
```json
{
  "incoming": [...],
  "outgoing": [...]
}
```

### POST /lending/protocol-history

Analyzes lending protocol interactions (Aave, Compound, etc.).

**Request:**
```json
{
  "wallet_address": "0x..."
}
```

**Response:** Protocol-level lending history with borrow/repay events.

### POST /aggregate

Aggregates all wallet data into a comprehensive profile.

**Request:**
```json
{
  "wallet_address": "0x..."
}
```

**Response:**
```json
{
  "wallet": "0x...",
  "nfts": {...},
  "tokens": {...},
  "eth_balance": "2.5",
  "defi_analysis": {...},
  "wallet_metadata": {...},
  "lending_history": {...}
}
```

## Data Sources

The service aggregates data from multiple sources:

- **Alchemy API**: Token balances, NFTs, transaction history, ETH balance
- **Etherscan API**: Detailed transaction events for lending protocol analysis
- **DeFi Protocols**: Aave V2/V3, Compound V2/V3, Uniswap V2/V3, Curve Finance
- **On-chain Analysis**: Asset transfers, contract interactions, approval behavior

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` file:

```
ALCHEMY_API_KEY=your_key_here
ALCHEMY_NETWORK=eth-mainnet
ETHERSCAN_API_KEY=your_key_here
```

3. Run:

```bash
uvicorn app:app --reload
```

## Key Features

### Advanced Lending Analysis

- **Repayment timeline tracking**: Monitors all borrow and repay events across protocols
- **Punctuality scoring**: Measures on-time repayment behavior
- **Protocol performance**: Analyzes repayment rates per protocol
- **Emergency detection**: Identifies urgent/last-minute repayment patterns

### Balance Sheet Assessment

- **Treasury NAV calculation**: Total net asset value across all holdings
- **Liquidity buffer analysis**: Cash reserves as percentage of total assets
- **Stress testing**: Portfolio resilience under market volatility scenarios
- **Diversification metrics**: Herfindahl index for concentration risk

### Capital Efficiency

- **Looping detection**: Identifies recursive borrow-deposit cycles
- **Debt service coverage**: Calculates DSCR based on cash flows
- **Token velocity**: Analyzes asset turnover patterns

## Limitations

- Transaction history limited by API rate limits
- Price data may be delayed or estimated
- Focuses on Ethereum mainnet only
- Lending analysis limited to tracked protocols (Aave, Compound)
