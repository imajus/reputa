# On-Chain Credit Score API

A FastAPI-based credit scoring system that analyzes Ethereum wallet behavior to generate a creditworthiness score (0-850, similar to FICO).

## Score Range

- **800-850**: Excellent (A+)
- **740-799**: Very Good (A)
- **670-739**: Good (B+)
- **580-669**: Fair (B)
- **500-579**: Poor (C)
- **400-499**: Very Poor (D)
- **0-399**: Bad (F)

## What Affects Your Score

### ✅ Positive Factors

#### Payment History (35% weight - Max 298 points)

- **DeFi Protocol Usage**
  - Aave interactions: +80 points
  - Compound interactions: +70 points
  - 3+ protocols: +50 points
- **Activity Consistency**
  - 12+ active months: +60 points
  - 6-12 active months: +30 points
- **Balanced Cash Flow**
  - ETH out/in ratio < 2: +38 points

#### Amounts Owed (30% weight - Max 255 points)

- **Stablecoin Holdings**
  - $10,000+: +100 points
  - $1,000-$10,000: +60 points
  - $100-$1,000: +30 points
- **Total Assets**: Up to +100 points (0.01 \* total USD value)
- **ETH Balance**
  - 10+ ETH: +55 points
  - 1-10 ETH: +35 points
  - 0.1-1 ETH: +15 points

#### Length of History (15% weight - Max 128 points)

- **Wallet Age**: +30 points per year (max 80 points at 2.5+ years)
- **Transaction Count**: +0.5 points per transaction (max 48 points)

#### New Credit (10% weight - Max 85 points)

- **Recent DeFi Activity**: +20 points per protocol (max 60)
- **Not Overextended**: +25 points if < 1000 transactions

#### Credit Mix (10% weight - Max 85 points)

- **Asset Diversification**: +15 points per asset type (tokens, NFTs, stablecoins, ETH)
- **Protocol Diversity**: +10 points per DeFi protocol (max 25)

#### Reputation Bonuses

- **POAPs**: +3 points each (max 40)
- **ENS Domain**: +25 points
- **Verified NFTs**: +5 points each (max 60)
- **Blue Chip NFTs**: +15 points each (max 50)
  - Bored Ape Yacht Club
  - CryptoPunks
  - Azuki
  - Mutant Ape Yacht Club
  - CloneX

### ❌ Negative Factors (Risk Penalties)

#### Critical Red Flags

- **Mixer Interaction**: -200 points
  - Tornado Cash or similar privacy protocols
  - Null address transactions

#### Suspicious Patterns

- **High Spam NFT Ratio**
  - > 50% spam: -80 points
  - 20-50% spam: -40 points
- **Drainer Pattern** (ETH out >> ETH in)
  - 10x+ outflow: -150 points
  - 5-10x outflow: -70 points
- **Low NFT Verification Rate**
  - <30% verified + 5+ NFTs: -30 points

## NFT Quality Assessment

### Verified NFTs (Best)

- `safelistRequestStatus: "verified"`
- Counts toward reputation
- Full value in scoring

### Not Requested (Neutral)

- `safelistRequestStatus: "not_requested"`
- Included in counts but no bonus
- Typical for smaller projects

### Spam NFTs (Negative)

- `isSpam: true` in contract or NFT metadata
- Not counted as legitimate
- Penalizes score if ratio too high

## DeFi Protocols Tracked

### Lending/Borrowing

- Aave V2 & V3
- Compound V2 & V3

### DEX

- Uniswap V2 & V3
- Curve Finance

## API Endpoints

### GET /score

Calculates comprehensive credit score for a wallet.

**Request:**

```json
{
  "wallet_address": "0x..."
}
```

**Response:**

```json
{
  "score": 720,
  "grade": "B+",
  "max_score": 850,
  "breakdown": {
    "payment_history": 180,
    "amounts_owed": 145,
    "length_of_history": 95,
    "new_credit": 60,
    "credit_mix": 70,
    "reputation_bonus": 85,
    "risk_penalty": -15
  },
  "details": {
    "total_assets_usd": 12500.5,
    "eth_balance": 2.4567,
    "stablecoin_balance_usd": 5000.0,
    "wallet_age_days": 856,
    "tx_count": 342,
    "active_months": 18,
    "defi_protocols_used": 3,
    "verified_nfts": 12,
    "blue_chip_nfts": 1,
    "poap_count": 15,
    "ens_count": 1
  },
  "risk_flags": {
    "mixer_transactions": false,
    "high_spam_ratio": false,
    "drainer_pattern": false,
    "low_nft_verification": false
  }
}
```

## Installation

1. Clone repository
2. Install dependencies:

```bash
pip install fastapi uvicorn requests pydantic-settings
```

3. Create `.env` file:

```
ALCHEMY_API_KEY=your_key_here
ALCHEMY_NETWORK=eth-mainnet
```

4. Run:

```bash
uvicorn app:app --reload
```

## Important Notes

### ENS and Credit Score

- **Yes, ENS affects your score** (+25 points bonus)
- ENS ownership shows:
  - Identity commitment
  - Reputation building
  - Long-term ecosystem participation

### ETH Balance

- **Yes, we check ETH balance** separately from ERC20 tokens
- Native ETH balance is fetched via `eth_getBalance`
- ERC20 tokens use `alchemy_getTokenBalances`
- Both contribute to "Amounts Owed" scoring category

### Stablecoins

- USDC, USDT, DAI tracked separately
- Shows liquidity and financial stability
- Major weight in "Amounts Owed" category

## Known Limitations

1. **No liquidation data** - Would require lending protocol event tracking
2. **Simplified DeFi analysis** - Only checks interactions, not loan health
3. **Price estimation** - Uses CoinGecko (rate limited) and OpenSea floor prices
4. **No gas analysis** - Could add commitment scoring
5. **Static mixer list** - Should integrate blockchain intelligence APIs

## Future Improvements

- [ ] Loan repayment history tracking
- [ ] Liquidation event detection
- [ ] Real-time gas spent analysis
- [ ] GitCoin donation tracking
- [ ] DAO governance participation
- [ ] Sybil attack detection
- [ ] Integration with Chainalysis/TRM Labs
