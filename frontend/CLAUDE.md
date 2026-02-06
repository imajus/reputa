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
- `suiAddress` - Connected Sui wallet address
- `txHash` - Transaction hash from recording on Sui

Access via `useReputa()` hook in any component.

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

**Sui Wallet Integration:**
- Uses `@mysten/dapp-kit` for wallet connection
- Connects to Sui testnet for score recording
- Transaction calls `update_wallet_score()` entry function

### Common Development Gotchas

- **CORS**: Oracle API must allow requests from `http://[::]:8080`
- **Wallet Connection**: Browser extension wallet (Sui Wallet) must be installed
- **Address Validation**: ENS resolution happens client-side before oracle query

### Configuration

- Development server runs on port 8080 with IPv6 (`::`), not the default Vite port
- HMR overlay is disabled in vite.config.ts
- TypeScript is configured with path alias `@/` pointing to `src/`
- Component tagging is enabled in development mode only (lovable-tagger)
- This project was scaffolded from Lovable.dev
