# Tasks: Enhance Oracle Scoring Framework

## Phase 1: Oracle Backend Updates

### Task 1: Create Helper Functions
- [ ] Add `formatQuestionnaireForAI(questionnaire)` function
  - Accept array of `{question, answer}` objects
  - Return formatted string `Q1: ...\nA1: ...\n\nQ2: ...`
  - Handle empty/null questionnaire → return "No questionnaire data provided."
  - Truncate extremely long answers (> 500 chars per answer)
- [ ] Add `validateScoreBreakdown(breakdown)` function
  - Accept breakdown object from AI response
  - Validate all 5 fields exist and are 0-100
  - Return defaults `{activity:50, maturity:50, diversity:50, riskBehavior:50, surveyMatch:50}` if invalid
  - Clamp values to 0-100 range
- [ ] Add `generateFallbackBreakdown(totalScore)` function
  - Accept total score (0-1000)
  - Return proportional breakdown based on score distribution weights
  - Set surveyMatch=50 (neutral when no AI)
- [ ] Add `sumField(protocols, field)` helper
  - Sum specific field across lending protocol objects
  - Used for calculating total borrow/repay/liquidate counts

**Validation:**
```bash
# Unit test the helpers
node -e "const {formatQuestionnaireForAI} = require('./src/index.js'); \
  console.log(formatQuestionnaireForAI([{question:'test', answer:'ans'}]))"
```

### Task 2: Replace Feature Extraction Function
- [ ] Rename `extractTransactionFeatures` → `extractWalletFeatures`
- [ ] Update function to parse new EVM data structure:
  - `wallet_metadata` → walletAge, totalTransactions, avgTxsPerMonth, uniqueCounterparties
  - `defi_analysis.protocol_interactions` → protocolsUsed, protocolNames, protocolDetails
  - `lending_history.protocol_analysis.protocols` → lending metrics (borrow/repay/liquidate/supply/withdraw counts)
  - `tokens.holdings` → numTokens, portfolioValueUSD
  - `tokens.concentration` → diversificationScore, concentrationRisk
  - `nfts` → poapCount, nftCount
  - `eth_balance` → ethBalance
- [ ] Remove old logic: timestamp parsing, protocol address detection
- [ ] Add error handling for missing fields (provide defaults)
- [ ] Return comprehensive feature object

**Validation:**
```bash
# Test with real n8n endpoint
curl -s "https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address=0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A" | \
  node -e "const {extractWalletFeatures} = require('./src/index.js'); \
    const data = JSON.parse(require('fs').readFileSync(0)); \
    console.log(JSON.stringify(extractWalletFeatures(data), null, 2))"
```

### Task 3: Enhance AI Scoring Function
- [ ] Add `questionnaire` parameter to `generateAIScore(features, questionnaire = [])`
- [ ] Call `formatQuestionnaireForAI(questionnaire)` to format Q&A
- [ ] Update AI prompt template:
  - Section 1: On-Chain Activity (wallet metadata, DeFi, lending, tokens, NFTs)
  - Section 2: Borrower Profile (formatted questionnaire)
  - Section 3: Scoring Instructions (5 dimensions with criteria)
- [ ] Update prompt scoring criteria:
  - Transaction Activity (0-100): count, frequency, recent engagement
  - Account Maturity (0-100): age, consistency
  - Protocol & Token Diversity (0-100): protocols, tokens, counterparties, concentration
  - Risk Behavior / Financial Health (0-100): liquidations, borrow/repay ratio, questionnaire liabilities
  - Questionnaire Coherence (0-100): intent alignment, or 50 if no questionnaire
- [ ] Update expected JSON output schema to include `scoreBreakdown` object
- [ ] Increase `num_predict` from 500 to 800 tokens
- [ ] Parse and validate `scoreBreakdown` from AI response
- [ ] Call `validateScoreBreakdown()` on result
- [ ] Update fallback to call `generateFallbackBreakdown()`

**Validation:**
```bash
# Test AI scoring with and without questionnaire
node -e "const {generateAIScore} = require('./src/index.js'); \
  const features = {walletAge:100, totalTransactions:500, ...}; \
  const q = [{question:'Who controls wallet?', answer:'individual'}]; \
  generateAIScore(features, q).then(r => console.log(JSON.stringify(r, null, 2)))"
```

### Task 4: Update POST /score Handler
- [ ] Extract `questionnaire` from request body (default to `[]`)
- [ ] Log whether questionnaire was provided
- [ ] Pass questionnaire to `generateAIScore(features, questionnaire)`
- [ ] Add `scoreBreakdown` to response metadata
- [ ] Keep `features` in metadata for debugging (optional)
- [ ] Ensure signature generation unchanged (score + address + timestamp only)
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
- [ ] Test GET endpoint still works (no questionnaire required)
- [ ] Verify scoreBreakdown generated even without questionnaire
- [ ] Confirm surveyMatch defaults to ~50 when no questionnaire

**Validation:**
```bash
curl "http://localhost:3000/score?address=0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A" \
  | jq '{score, breakdown: .metadata.scoreBreakdown}'
```

## Phase 2: Frontend Updates

### Task 6: Update TypeScript Interfaces
- [ ] Edit `frontend/src/lib/api.ts`
- [ ] Extend `ScoreResponse` interface with optional `metadata` field
- [ ] Define metadata structure:
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
- [ ] Edit `frontend/src/pages/Analyzing.tsx`
- [ ] Delete lines 51-57 (random score generation)
- [ ] Parse `scoreBreakdown` from API response: `response.metadata?.scoreBreakdown`
- [ ] Provide fallback defaults if breakdown missing:
  ```javascript
  const scoreBreakdown = response.metadata?.scoreBreakdown || {
    activity: 50,
    maturity: 50,
    diversity: 50,
    riskBehavior: 50,
    surveyMatch: 50
  };
  ```
- [ ] Optional: Log metadata for debugging (reasoning, risk_factors, strengths)

**Validation:**
```bash
# Start dev server and complete flow
cd frontend && npm run dev
# Enter address → answer questionnaire → verify non-random scores displayed
```

### Task 8: Optional UI Enhancements
- [ ] Update ScoreReview.tsx labels for clarity:
  - "Activity Score" → "Transaction Activity"
  - "Risk Behavior" → "Financial Health" or "Creditworthiness"
  - "Survey Match" → "Intent Alignment"
- [ ] Add tooltips explaining each dimension
- [ ] Consider displaying questionnaire impact explicitly

**Validation:**
```bash
# Visual verification: labels are clear and user-friendly
```

## Phase 3: Testing & Validation

### Task 9: Oracle Integration Tests
- [ ] Test with real EVM address and full questionnaire:
  ```bash
  curl -X POST http://localhost:3000/score \
    -H "Content-Type: application/json" \
    -d '{
      "address": "0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A",
      "questionnaire": [
        {"question": "Who controls this wallet?", "answer": "individual"},
        {"question": "What is the loan for?", "answer": "working capital"}
      ]
    }' | jq '.'
  ```
- [ ] Verify response includes:
  - `score` (0-1000)
  - `signature` (hex string)
  - `metadata.scoreBreakdown` (5 fields, all 0-100)
  - `metadata.reasoning` (string)
- [ ] Test with empty questionnaire:
  ```bash
  curl -X POST http://localhost:3000/score \
    -H "Content-Type: application/json" \
    -d '{"address":"0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A","questionnaire":[]}' \
    | jq '.metadata.scoreBreakdown.surveyMatch'
  # Should be ~50
  ```
- [ ] Test with missing questionnaire field:
  ```bash
  curl -X POST http://localhost:3000/score \
    -H "Content-Type: application/json" \
    -d '{"address":"0x859e1Dfb430A7156fAEF11947F2FC2a3C34B733A"}' \
    | jq '.metadata.scoreBreakdown'
  # Should still return valid breakdown
  ```

### Task 10: End-to-End Frontend Testing
- [ ] Complete full user flow:
  1. Navigate to landing page
  2. Enter EVM address
  3. Answer all 6 questionnaire questions
  4. Wait for analysis (should complete in <10s)
  5. View ScoreReview page
- [ ] Verify scoreBreakdown displays:
  - All 5 scores are visible
  - Scores are NOT random (repeat flow, verify consistency for same inputs)
  - Progress bars match numeric values
- [ ] Check browser console:
  - No errors
  - "Oracle response:" log shows metadata.scoreBreakdown
  - Optional: reasoning and risk_factors logged
- [ ] Test edge cases:
  - Skip all questionnaire questions → surveyMatch should be ~50
  - Same address, different answers → different riskBehavior/surveyMatch

### Task 11: Comparative Validation
- [ ] Test same address with different questionnaire answers:
  ```bash
  # Test 1: Complete questionnaire
  curl -X POST ... # Full questionnaire
  # Test 2: Empty questionnaire
  curl -X POST ... # Empty array
  # Verify: surveyMatch and riskBehavior differ
  ```
- [ ] Test wallet with liquidation history:
  - Find address with liquidations in n8n data
  - Verify riskBehavior score is lower than clean wallet
- [ ] Test wallet with high protocol diversity:
  - Use address with 5+ protocols
  - Verify diversity score is high (>70)
- [ ] Test new wallet (<100 txs):
  - Verify activity and maturity scores are low (<50)

### Task 12: Performance & Reliability Checks
- [ ] Measure API response time:
  ```bash
  time curl -X POST http://localhost:3000/score ...
  # Should be < 10 seconds
  ```
- [ ] Monitor Ollama logs for errors
- [ ] Check memory usage during scoring (should stay under 6GB)
- [ ] Verify health endpoint:
  ```bash
  curl http://localhost:3000/health
  # Should show ollama: "connected"
  ```
- [ ] Test fallback mechanism:
  - Stop Ollama service temporarily
  - Verify oracle returns fallback breakdown
  - Check logs for fallback message

## Phase 4: Documentation & Deployment

### Task 13: Update Documentation
- [ ] Update `oracle/CLAUDE.md`:
  - Document new EVM data structure
  - Explain scoreBreakdown fields
  - Add questionnaire integration notes
- [ ] Update `frontend/CLAUDE.md`:
  - Remove reference to random score generation
  - Document scoreBreakdown parsing
- [ ] Update main `CLAUDE.md`:
  - Reflect enhanced scoring capabilities
  - Note questionnaire influence on scores

### Task 14: Pre-Deployment Validation
- [ ] Run full test suite locally
- [ ] Verify TypeScript compilation: `cd frontend && npm run build`
- [ ] Test oracle with curl against test address
- [ ] Ensure no breaking changes to signature format
- [ ] Confirm backward compatibility (GET /score works)

### Task 15: Deploy & Monitor
- [ ] Deploy updated oracle to TEE
- [ ] Verify PCR attestation updates correctly
- [ ] Test deployed endpoint with curl
- [ ] Deploy frontend
- [ ] Monitor for errors in production
- [ ] Collect user feedback on score accuracy

## Success Checklist

After completing all tasks, verify:

- [ ] Oracle parses new EVM data structure without errors
- [ ] POST /score returns metadata.scoreBreakdown with 5 numeric values (0-100)
- [ ] GET /score still works (backward compatible)
- [ ] Frontend displays non-random breakdown scores
- [ ] Empty/missing questionnaire doesn't crash
- [ ] Same address + different questionnaires → different scores
- [ ] Liquidation history → lower riskBehavior
- [ ] High protocol diversity → higher diversity score
- [ ] API response time < 10 seconds
- [ ] Signature verification unchanged
- [ ] No console errors in frontend
- [ ] Ollama health checks pass
