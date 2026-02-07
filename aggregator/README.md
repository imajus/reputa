# On-Chain Credit Assessment System

Comprehensive credit analysis for Ethereum wallets. Scores range from 300-850 (similar to FICO), combining behavioral patterns with institutional-grade assessment across lending, treasury, capital usage, and cash flows.

**Grades:** S-tier (800+), A-tier (700-799), B-tier (600-699), C-tier (500-599), D-tier (300-499)

---

## Assessment Framework

### 1. Past Credit Performance (35%)

**Repayment History**
- Borrow and repay event tracking across Aave, Compound, Morpho
- Repayment ratio and timeline analysis
- Liquidation and default detection

**Behavioral Patterns**
- Punctuality scoring (early/on-time/late repayments)
- Emergency repayment detection (< 24hr turnaround)
- Borrowing frequency and trend analysis
- Protocol performance comparison

**Market Stress Response**
- Crisis behavior tracking
- Multi-protocol diversification
- Lending venue performance consistency

---

### 2. Balance Sheet Analysis (25%)

**Portfolio Composition**
- Full token inventory with categorization (stables, governance, LSDs, wrapped)
- NFT holdings with floor price valuation
- Treasury NAV calculation

**Risk Metrics**
- Volatility analysis (30-day historical)
- Concentration risk (Herfindahl index)
- Asset-liability alignment
- Liquidity buffer measurement

**Stress Testing**
- Price shock scenarios (-30%, -50%, -70%)
- Market downturn resilience
- Expected runway calculation

---

### 3. Use of Proceeds (20%)

**Capital Allocation**
- Leverage pattern detection
- Recursive borrowing identification (supply → borrow loops)
- Capital efficiency analysis

**Strategy Classification**
- Productive vs. speculative usage
- Protocol interaction patterns
- Leverage strategy type

---

### 4. Cash Flow Analysis (20%)

**Debt Service Capacity**
- Coverage ratio estimation
- Revenue proxy calculation
- Payment capacity assessment

**Resilience Modeling**
- Revenue stress scenarios
- Solvency breakpoint analysis
- Cash flow sustainability

---

## Scoring Components

### Payment History (298 pts)
- Lending track record: 150 pts
- Protocol usage (Aave +20, Compound +15, Morpho +10): 80 pts
- Consistent activity (12+ months, 5+ tx/mo): 60 pts

### Amounts Owed (255 pts)
- Stablecoin liquidity (20-50% optimal): 100 pts
- Total assets ($1 = 0.01 pts): 100 pts
- ETH balance (10+ ETH max): 55 pts

### Credit History (128 pts)
- Wallet age (30 pts/year): 80 pts
- Transaction count (0.5 pts/tx): 48 pts

### Diversification (85 pts)
- Protocol mix: 60 pts
- Asset variety: 25 pts

### Credit Mix (85 pts)
- Portfolio Herfindahl index: 40 pts
- DeFi engagement: 45 pts

### Reputation Signals (200 pts)
- POAPs: +3 each (max 40)
- ENS ownership: +25
- Verified NFTs: +5 each (max 60)
- Blue chips (BAYC, Punks, Azuki, MAYC, CloneX): +15 each (max 50)
- Active staking: +5 each (max 30)
- Clean lending history: +40

### Risk Penalties
- Mixer interactions (Tornado Cash): -200
- Portfolio concentration (>50% single asset): -100
- High volatility exposure: -80
- Spam NFT ratio: -80
- Drainer pattern (10x+ ETH outflow): -150
- Liquidation history: -30 per event

---

## Data Sources

**Alchemy:** Token balances, NFT inventory, prices, transfer history  
**Etherscan:** Transaction history, function signatures  
**OpenSea:** NFT floor prices, verification status

---

## Tracked Protocols

**Lending:** Aave V2/V3, Compound V2/V3, Morpho Blue, Spark  
**Staking:** Ethena (USDe, deUSD), Lido (stETH)  
**DEX:** Uniswap, Curve  
**Privacy:** Tornado Cash detection

---

## API Endpoints

### POST /score
Quick behavioral score (0-850).

Returns: Score, grade, breakdown, portfolio analysis, credit history, risk flags

### POST /assessment
Institutional credit assessment (300-850).

Returns: Detailed analysis across 4 categories with timelines, punctuality metrics, stress tests, looping detection, and DSCR calculations

**Request:**
```json
{"wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
```

---

## Installation

```bash
pip install fastapi uvicorn requests pydantic-settings web3
```

**.env:**
```env
ALCHEMY_API_KEY=your_key
ETHERSCAN_API_KEY=your_key
ALCHEMY_NETWORK=eth-mainnet
```

**Run:**
```bash
uvicorn app:app --reload
```

---

## Response Fields

### Quick Score
- `score` (0-850)
- `grade` (AAA to F)
- `breakdown` (payment, amounts, history, mix, reputation, penalties)
- `credit_history` (borrows, repays, liquidations, protocols)
- `portfolio_analysis` (diversification, concentration, volatility)
- `risk_flags` (mixer, spam, drainer, concentration, liquidations)

### Institutional Assessment
- `credit_score` (300-850 with component breakdown)
- `1_past_credit_performance` (timelines, punctuality, frequency, emergencies, protocol performance)
- `2_balance_sheet` (NAV, liquidity buffers, stress tests)
- `3_use_of_proceeds` (looping detection, leverage strategy)
- `4_cash_flows` (DSCR, stress scenarios, resilience)

---

**Built for:** DeFi lending protocols, credit underwriters, risk analysts  
**Best for:** Behavioral screening, pattern detection, portfolio analysis  
**Use with:** On-chain data enrichment for comprehensive credit decisions

---

*Experimental research software. Not financial advice.*
