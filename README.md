# On-Chain Credit Scoring System

A blockchain-based credit scoring system that analyzes Ethereum wallet activity to generate creditworthiness scores (300-850 range, similar to traditional FICO scores).

## Overview

This system fetches on-chain data using Alchemy API and calculates a comprehensive credit score based on:

- **Wallet Age**: How long the wallet has been active
- **Asset Holdings**: ETH, ERC20 tokens, NFTs, and their USD values
- **Transaction Activity**: Volume, frequency, and recency of transactions
- **DeFi Participation**: Active positions in DeFi protocols
- **Community Engagement**: POAPs (Proof of Attendance Protocol badges) from events
- **Identity**: ENS domain ownership
- **Risk Factors**: Interactions with known scam addresses or mixers

## Features

- ✅ **Alchemy-Only Integration** - No Etherscan dependency
- ✅ **Comprehensive Asset Tracking** - Tokens, NFTs, POAPs, ENS
- ✅ **Scam Detection** - Flags interactions with known malicious addresses
- ✅ **Mixer Detection** - Identifies privacy mixer usage (Tornado Cash, etc.)
- ✅ **REST API** - FastAPI-based endpoints for easy integration
- ✅ **Credit Score (300-850)** - Industry-standard score range with grade (AAA-F)

## Architecture

```
┌─────────────────┐
│   Alchemy API   │  ← Single data source
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DataAggregator  │  ← Fetches wallet data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CreditScorer    │  ← Calculates score
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  ← REST endpoints
└─────────────────┘
```

## Configuration

Create a `.env` file:

```env
ALCHEMY_API_KEY=your_alchemy_key_here
```

## Usage

### Run the API Server

```bash
uvicorn src.api:app --reload
```

Server starts at `http://localhost:8000`

### API Endpoints

#### Get Wallet Credit Score

```bash
GET /wallets/{address}/score
```

Returns complete wallet profile with credit score, breakdown, and asset summary.

Example:

```bash
curl http://localhost:8000/wallets/0x0000000000000000000000000000000000000000/score
```

#### Get Score Breakdown Only

```bash
GET /wallets/{address}/breakdown
```

Returns just the score components without full asset details (lighter query).

#### Get Wallet Assets

```bash
GET /wallets/{address}/assets
```

Returns detailed listing of all assets: tokens, NFTs, POAPs, DeFi positions, and recent transactions.

### API Documentation

Interactive API documentation available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Scoring Methodology

### Score Components (Max 850 points)

| Component          | Max Points | Description                                      |
| ------------------ | ---------- | ------------------------------------------------ |
| Wallet Age         | 100        | Age in days (2+ years = max)                     |
| Assets             | 200        | ETH, tokens, NFTs value                          |
| Activity           | 150        | Transaction count, volume, recency               |
| POAPs              | 100        | Event attendance, categories                     |
| ENS                | 50         | ENS domain ownership                             |
| DeFi               | 100        | DeFi protocol participation                      |
| RWAs               | 50         | Real World Asset holdings                        |
| **Risk Penalties** | -∞         | Scam interactions (-100 each), mixer usage (-50) |

### Risk Levels

| Score Range | Grade | Risk Level |
| ----------- | ----- | ---------- |
| 750-850     | AAA-A | Low        |
| 650-749     | BBB-B | Medium     |
| 550-649     | CCC-C | High       |
| 300-549     | D-F   | Very High  |

## Data Sources

All data fetched from **Alchemy API**:

- `eth_getBalance` - ETH balance
- `alchemy_getTokenBalances` - ERC20 tokens
- `getNFTsForOwner` - NFTs, POAPs, ENS names
- `alchemy_getAssetTransfers` - Transaction history
- `alchemy_getTokenMetadata` - Token information

## Example Response

```json
{
  "address": "0x0000000000000000000000000000000000000000",
  "credit_score": 720,
  "grade": "A",
  "breakdown": {
    "wallet_age": 85.0,
    "assets": 120.0,
    "activity": 95.0,
    "poaps": 45.0,
    "ens": 30.0,
    "defi": 0.0,
    "rwa": 0.0,
    "risk_penalty": 0.0
  },
  "total_value": 2547.33,
  "token_count": 4,
  "nft_count": 2,
  "wallet_age_days": 856,
  "transaction_count": 7
}
```

## Project Structure

```
.
├── src/
│   ├── api.py              # FastAPI REST endpoints
│   ├── data_aggregator.py  # Alchemy data fetching
│   ├── credit_scorer.py    # Score calculation logic
│   └── config.py           # Configuration settings
├── README.md
└── requirements.txt
```

## Requirements

```
fastapi>=0.104.0
uvicorn>=0.24.0
aiohttp>=3.9.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```
