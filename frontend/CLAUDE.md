# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
npm i                    # Install dependencies
npm run dev             # Start development server on http://[::]:8080
npm run build           # Production build
npm run build:dev       # Development mode build
npm run lint            # Run ESLint
npm test                # Run tests once with Vitest
npm run test:watch      # Run tests in watch mode
npm run preview         # Preview production build
```

## Architecture

### Tech Stack
- **Build Tool**: Vite with React SWC plugin
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **UI Library**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS with custom theme
- **State Management**: React Context API (ReputaContext)
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form with Zod validation
- **Testing**: Vitest with React Testing Library
- **Blockchain**:
  - EVM: RainbowKit + wagmi (wallet connection for address input)
  - Sui: @mysten/dapp-kit + @mysten/sui (wallet connection and transactions)

### Project Structure

```
src/
├── components/
│   ├── landing/        # Landing page specific components
│   ├── layout/         # Layout components (Header, Footer, Layout wrapper)
│   └── ui/             # shadcn/ui components (generated, avoid editing directly)
├── contexts/           # React contexts (ReputaContext for global state)
├── hooks/              # Custom React hooks
├── lib/                # Utility functions
├── pages/              # Route page components
└── test/               # Test setup and test files
```

### Application Flow

This is a DeFi reputation migration application with the following user journey:

1. **Landing** (`/`) - Marketing page introducing the service
2. **AddressInput** (`/analyze`) - User enters EVM address or ENS name
3. **Questionnaire** (`/questionnaire`) - User answers DeFi experience questions
4. **Analyzing** (`/analyzing`) - Processing/analysis loading state
5. **ScoreReview** (`/score`) - Display calculated reputation score with breakdown
6. **WalletConnect** (`/record`) - User connects Sui wallet to record score
7. **Success** (`/success`) - Confirmation of successful migration
8. **DemoProtocol** (`/demo`) - Demo of protocol integration

### Global State (ReputaContext)

The `ReputaContext` manages the entire user flow state:

- `evmAddress` - Original EVM address input
- `resolvedAddress` - Resolved address (from ENS if applicable)
- `questionnaire` - User's DeFi experience answers (experience, activities, risk tolerance, etc.)
- `score` - Overall reputation score (0-1000) from oracle AI analysis
- `scoreBreakdown` - Component scores (activity, maturity, diversity, riskBehavior, surveyMatch), each 0-100
- `oracleSignature` - TEE oracle signature (hex string) for on-chain verification
- `oracleTimestamp` - Timestamp (ms) when score was signed by oracle
- `suiAddress` - Connected Sui wallet address
- `txHash` - Transaction hash from recording on Sui

Access via `useReputa()` hook in any component.

**Methods:**
- `setEvmAddress(address)` - Store EVM address input
- `setResolvedAddress(address)` - Store ENS-resolved address
- `updateQuestionnaire(answers)` - Store questionnaire responses
- `setScore(score, breakdown)` - Store score and breakdown from oracle
- `setOracleData(signature, timestamp)` - Store oracle signature and timestamp
- `setSuiAddress(address)` - Store connected Sui wallet address
- `setTxHash(hash)` - Store transaction digest
- `reset()` - Clear all state

### Styling

- Uses Tailwind CSS with custom design tokens defined in CSS variables
- Theme extends with custom colors, shadows, fonts (Inter, Lora, Space Mono)
- All components use `@/` alias for imports (resolves to `src/`)
- shadcn/ui components in `src/components/ui/` are generated - modify the source generator config instead

### Testing

- Tests go in `src/**/*.{test,spec}.{ts,tsx}`
- Setup file at `src/test/setup.ts` configures jsdom and jest-dom
- Use `@testing-library/react` for component testing
- matchMedia is mocked in setup for components using media queries

## Important Notes

### Oracle Integration

The frontend integrates with the oracle backend for reputation scoring:

**API Endpoints:**
- `GET /score?address=0x...` - Get score without questionnaire (backward compatible)
- `POST /score` - Get score with questionnaire data

**POST Request Format:**
```json
{
  "address": "0x...",
  "questionnaire": [
    {"question": "Who controls this wallet?", "answer": "individual"},
    {"question": "What is the loan for?", "answer": "working capital"}
  ]
}
```

**Response Format:**
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
    "reasoning": "Account shows strong engagement...",
    "risk_factors": ["High token concentration"],
    "strengths": ["Consistent repayment history"]
  }
}
```

**Score Breakdown Parsing:**

The `Analyzing.tsx` page parses the scoreBreakdown from the API response:

```typescript
const scoreBreakdown = response.metadata?.scoreBreakdown || {
  activity: 50,
  maturity: 50,
  diversity: 50,
  riskBehavior: 50,
  surveyMatch: 50
};
```

Fallback defaults are provided if the breakdown is missing. The breakdown is then displayed in `ScoreReview.tsx` with descriptive labels:
- **Transaction Activity**: Transaction count, frequency, recent engagement
- **Account Maturity**: Account age, usage consistency
- **Protocol & Token Diversity**: Protocol count, token diversification, unique counterparties
- **Financial Health**: Liquidations, borrow/repay ratio, liability disclosure
- **Intent Alignment**: Coherence between stated intent and on-chain behavior

### Sui Wallet Integration

The application uses `@mysten/dapp-kit` for Sui blockchain integration, enabling users to record their reputation scores on-chain with cryptographic proof from the TEE oracle.

**Architecture:**

```
Oracle API → Sign (score + address + timestamp) → Frontend
                                                       ↓
                                          Sui Wallet Connection
                                                       ↓
                                          Transaction Construction
                                                       ↓
                                          update_wallet_score()
                                                       ↓
                                          On-Chain Verification
```

**Key Files:**
- `src/lib/suiNetwork.ts` - Network configuration (testnet/mainnet)
- `src/lib/oracleService.ts` - Oracle API client and utilities
- `src/types/oracle.d.ts` - TypeScript interfaces for oracle responses
- `src/pages/WalletConnect.tsx` - Wallet connection and transaction signing
- `src/contexts/ReputaContext.tsx` - Stores oracle signature and timestamp

**Transaction Flow:**

1. **Oracle Signing** (`Analyzing.tsx`):
   - Calls oracle API with EVM address and questionnaire
   - Receives score, signature, timestamp, and metadata
   - Stores `oracleSignature` and `oracleTimestamp` in ReputaContext

2. **Wallet Connection** (`WalletConnect.tsx`):
   - Uses `ConnectButton` from dapp-kit for wallet selection
   - Supports Sui Wallet, Suiet, Ethos, and other standard wallets
   - Syncs connected address to ReputaContext automatically

3. **Transaction Construction**:
   - Builds `Transaction` object with `moveCall` to `update_wallet_score`
   - Converts wallet address string to UTF-8 bytes (not hex-decoded!)
   - Converts signature hex to bytes using `hexToUint8Array()`
   - Uses BCS serialization for `vector<u8>` arguments

4. **Signature Verification On-Chain**:
   - Move contract verifies TEE signature using enclave public key
   - Stores score with wallet address and timestamp
   - Returns transaction digest for explorer link

**Important Implementation Details:**

- **Address Encoding**: The wallet address must be UTF-8 string bytes, NOT hex-decoded bytes
  ```typescript
  // Correct - UTF-8 encoding of the string "0xabc..."
  const addressBytes = new TextEncoder().encode(walletAddressString);

  // Wrong - hex-decoded bytes (causes MoveAbort in string::utf8)
  const addressBytes = hexToUint8Array(walletAddressString);
  ```

- **BCS Serialization**: Use `bcs.vector(bcs.u8()).serialize()` for byte arrays
  ```typescript
  tx.pure(bcs.vector(bcs.u8()).serialize(Array.from(bytes)))
  ```

- **Navigation Guards**: `/record` page redirects to `/analyze` if oracle data is missing

**Environment Variables:**

Required variables in `.env.local`:

```bash
# Oracle API Configuration
VITE_ORACLE_API_URL=http://3.111.136.41:3000  # TEE oracle endpoint

# Sui Network Configuration
VITE_SUI_NETWORK=testnet                       # Network (testnet/mainnet)
VITE_ORACLE_PACKAGE_ID=0xb39cd9c48c27...       # Published Move package ID
VITE_ORACLE_OBJECT_ID=0xcca4998944cdfd...      # Shared ScoreOracle object
VITE_ENCLAVE_OBJECT_ID=0xe03cfc8ae573fc...     # Shared Enclave object

# EVM Wallet (RainbowKit)
VITE_WALLETCONNECT_PROJECT_ID=6e54538f0b06...  # WalletConnect project ID
```

**How to Get Object IDs:**
- Package ID: From `sui client publish` output
- Oracle Object ID: From running oracle deployment script
- Enclave Object ID: From oracle registration on-chain

### Common Development Gotchas

- **CORS**: Oracle API must allow requests from `http://[::]:8080`
- **Wallet Connection**: Browser extension wallet (Sui Wallet) must be installed for testing
- **Address Validation**: ENS resolution happens client-side before oracle query
- **BCS Encoding**: Always use BCS serialization for `vector<u8>` arguments in transactions
- **String vs Bytes**: Wallet address is UTF-8 string bytes, signature is hex-decoded bytes

### Troubleshooting

**Issue: `CommandArgumentError: InvalidBCSBytes`**
- **Cause**: Incorrect BCS serialization of transaction arguments
- **Solution**: Use `bcs.vector(bcs.u8()).serialize(Array.from(bytes))` for byte arrays
- **Check**: Verify you're passing `Uint8Array` wrapped in BCS serialization

**Issue: `MoveAbort in string::utf8`**
- **Cause**: Wallet address passed as hex-decoded bytes instead of UTF-8 string bytes
- **Solution**: Use `new TextEncoder().encode(addressString)` not `hexToUint8Array()`
- **Explanation**: Move contract calls `to_string()` which requires valid UTF-8

**Issue: Wallet not connecting**
- **Cause**: No Sui wallet extension installed
- **Solution**: Install [Sui Wallet](https://chrome.google.com/webstore/detail/sui-wallet/) browser extension
- **Alternative**: Use Suiet or Ethos Wallet

**Issue: Transaction signature verification fails on-chain**
- **Cause**: Mismatch between signed data and transaction data
- **Solution**: Ensure `score`, `wallet_address`, and `timestamp_ms` match oracle response exactly
- **Check**: Verify oracle signature in ReputaContext matches the one being sent

**Issue: Cannot access `/record` page**
- **Cause**: Missing oracle signature or score in ReputaContext
- **Solution**: Complete the flow from `/analyze` → `/questionnaire` → `/analyzing` first
- **Check**: Navigation guard redirects if `state.score` or `state.oracleSignature` is empty

**Issue: Explorer link doesn't work**
- **Cause**: Transaction hash not stored or network mismatch
- **Solution**: Verify `VITE_SUI_NETWORK` matches deployment network (testnet/mainnet)
- **Check**: Transaction digest should appear in ReputaContext after successful signing

### Configuration

- Development server runs on port 8080 with IPv6 (`::`), not the default Vite port
- HMR overlay is disabled in vite.config.ts
- TypeScript is configured with path alias `@/` pointing to `src/`
- Component tagging is enabled in development mode only (lovable-tagger)
- This project was scaffolded from Lovable.dev
