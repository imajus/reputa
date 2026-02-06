# Tasks: Enhance Oracle Scoring Framework

## Phase 1: Oracle Backend Updates

### Task 1: Create Helper Functions
- [x] Add `formatQuestionnaireForAI(questionnaire)` function
  - Accept array of `{question, answer}` objects
  - Return formatted string `Q1: ...\nA1: ...\n\nQ2: ...`
  - Handle empty/null questionnaire → return "No questionnaire data provided."
  - Truncate extremely long answers (> 500 chars per answer)
- [x] Add `validateScoreBreakdown(breakdown)` function
  - Accept breakdown object from AI response
  - Validate all 5 fields exist and are 0-100
  - Return defaults `{activity:50, maturity:50, diversity:50, riskBehavior:50, surveyMatch:50}` if invalid
  - Clamp values to 0-100 range
- [x] Add `generateFallbackBreakdown(totalScore)` function
  - Accept total score (0-1000)
  - Return proportional breakdown based on score distribution weights
  - Set surveyMatch=50 (neutral when no AI)
- [x] Add `sumField(protocols, field)` helper
  - Sum specific field across lending protocol objects
  - Used for calculating total borrow/repay/liquidate counts

**Validation:**
```bash
# Unit test the helpers
node -e "const {formatQuestionnaireForAI} = require('./src/index.js'); \
  console.log(formatQuestionnaireForAI([{question:'test', answer:'ans'}]))"
```

### Task 2: Replace Feature Extraction Function
- [x] Rename `extractTransactionFeatures` → `extractWalletFeatures`
- [x] Update function to parse new EVM data structure:
  - `wallet_metadata` → walletAge, totalTransactions, avgTxsPerMonth, uniqueCounterparties
  - `defi_analysis.protocol_interactions` → protocolsUsed, protocolNames, protocolDetails
  - `lending_history.protocol_analysis.protocols` → lending metrics (borrow/repay/liquidate/supply/withdraw counts)
  - `tokens.holdings` → numTokens, portfolioValueUSD
  - `tokens.concentration` → diversificationScore, concentrationRisk
  - `nfts` → poapCount, nftCount
  - `eth_balance` → ethBalance
- [x] Remove old logic: timestamp parsing, protocol address detection
- [x] Add error handling for missing fields (provide defaults)
- [x] Return comprehensive feature object

**Validation:**
```bash
# Test with real n8n endpoint
curl -s "https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address=0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A" | \
  node -e "const {extractWalletFeatures} = require('./src/index.js'); \
    const data = JSON.parse(require('fs').readFileSync(0)); \
    console.log(JSON.stringify(extractWalletFeatures(data), null, 2))"
```

### Task 3: Enhance AI Scoring Function
- [x] Add `questionnaire` parameter to `generateAIScore(features, questionnaire = [])`
- [x] Call `formatQuestionnaireForAI(questionnaire)` to format Q&A
- [x] Update AI prompt template:
  - Section 1: On-Chain Activity (wallet metadata, DeFi, lending, tokens, NFTs)
  - Section 2: Borrower Profile (formatted questionnaire)
  - Section 3: Scoring Instructions (5 dimensions with criteria)
- [x] Update prompt scoring criteria:
  - Transaction Activity (0-100): count, frequency, recent engagement
  - Account Maturity (0-100): age, consistency
  - Protocol & Token Diversity (0-100): protocols, tokens, counterparties, concentration
  - Risk Behavior / Financial Health (0-100): liquidations, borrow/repay ratio, questionnaire liabilities
  - Questionnaire Coherence (0-100): intent alignment, or 50 if no questionnaire
- [x] Update expected JSON output schema to include `scoreBreakdown` object
- [x] Increase `num_predict` from 500 to 800 tokens
- [x] Parse and validate `scoreBreakdown` from AI response
- [x] Call `validateScoreBreakdown()` on result
- [x] Update fallback to call `generateFallbackBreakdown()`

**Validation:**
```bash
# Test AI scoring with and without questionnaire
node -e "const {generateAIScore} = require('./src/index.js'); \
  const features = {walletAge:100, totalTransactions:500, ...}; \
  const q = [{question:'Who controls wallet?', answer:'individual'}]; \
  generateAIScore(features, q).then(r => console.log(JSON.stringify(r, null, 2)))"
```

### Task 4: Update POST /score Handler
- [x] Extract `questionnaire` from request body (default to `[]`)
- [x] Log whether questionnaire was provided
- [x] Pass questionnaire to `generateAIScore(features, questionnaire)`
- [x] Add `scoreBreakdown` to response metadata
- [x] Keep `features` in metadata for debugging (optional)
- [x] Ensure signature generation unchanged (score + address + timestamp only)
- [ ] Test with curl:
  ```bash
  curl -X POST http://localhost:3000/score \
    -H "Content-Type: application/json" \
    -d '{"address":"0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A", \
         "questionnaire":[{"question":"test","answer":"ans"}]}'
  ```

**Validation:**
```bash
# Response must include metadata.scoreBreakdown with 5 numeric fields
curl -X POST http://localhost:3000/score \
  -H "Content-Type: application/json" \
  -d '{"address":"0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A", "questionnaire":[]}' \
  | jq '.metadata.scoreBreakdown'
```

### Task 5: Verify GET /score Backward Compatibility
- [x] Test GET endpoint still works (no questionnaire required)
- [x] Verify scoreBreakdown generated even without questionnaire
- [x] Confirm surveyMatch defaults to ~50 when no questionnaire

**Validation:**
```bash
curl "http://localhost:3000/score?address=0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A" \
  | jq '{score, breakdown: .metadata.scoreBreakdown}'
```

## Phase 2: Frontend Updates

### Task 6: Update TypeScript Interfaces
- [x] Edit `frontend/src/lib/api.ts`
- [x] Extend `ScoreResponse` interface with optional `metadata` field
- [x] Define metadata structure:
  ```typescript
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
  }
  ```

**Validation:**
```bash
# TypeScript compilation should pass
cd frontend && npm run build
```

### Task 7: Remove Random Score Generation
- [x] Edit `frontend/src/pages/Analyzing.tsx`
- [x] Delete lines 51-57 (random score generation)
- [x] Parse `scoreBreakdown` from API response: `response.metadata?.scoreBreakdown`
- [x] Provide fallback defaults if breakdown missing:
  ```javascript
  const scoreBreakdown = response.metadata?.scoreBreakdown || {
    activity: 50,
    maturity: 50,
    diversity: 50,
    riskBehavior: 50,
    surveyMatch: 50
  };
  ```
- [x] Optional: Log metadata for debugging (reasoning, risk_factors, strengths)

**Validation:**
```bash
# Start dev server and complete flow
cd frontend && npm run dev
# Enter address → answer questionnaire → verify non-random scores displayed
```

### Task 8: Optional UI Enhancements
- [x] Update ScoreReview.tsx labels for clarity:
  - "Activity Score" → "Transaction Activity"
  - "Risk Behavior" → "Financial Health"
  - "Survey Match" → "Intent Alignment"
- [ ] Add tooltips explaining each dimension
- [ ] Consider displaying questionnaire impact explicitly

**Validation:**
```bash
# Visual verification: labels are clear and user-friendly
```

## Phase 3: Documentation

### Task 9: Update Documentation
- [x] Update `oracle/CLAUDE.md`:
  - Document new EVM data structure
  - Explain scoreBreakdown fields
  - Add questionnaire integration notes
- [x] Update `frontend/CLAUDE.md`:
  - Remove reference to random score generation
  - Document scoreBreakdown parsing
- [x] Update main `CLAUDE.md`:
  - Reflect enhanced scoring capabilities
  - Note questionnaire influence on scores

