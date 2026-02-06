# Proposal: Enhance Oracle Scoring Framework with Rich EVM Data & Questionnaire Integration

## Problem Statement

The oracle scoring system currently has two major gaps:

1. **Outdated Data Structure**: The oracle expects `EVM.Events[]` format (block timestamps, contract addresses, transaction values), but the n8n endpoint now returns rich analytical data including:
   - Pre-calculated wallet metadata (age, transaction counts, unique counterparties)
   - DeFi protocol interactions (Aave, Compound, Uniswap, Curve, Morpho)
   - Detailed lending history (borrow/repay/liquidate/supply/withdraw counts)
   - Token portfolio metrics (holdings, concentration, diversification scores)
   - NFT ownership and POAPs

2. **Ignored Questionnaire Data**: The frontend sends borrower questionnaire responses (wallet control, loan purpose, revenue streams, liabilities, beneficial ownership) to the `/score` endpoint, but the AI scoring prompt doesn't incorporate this data. This misses critical creditworthiness signals that complement on-chain behavior.

3. **Missing Score Breakdown**: The frontend displays random placeholder scores for activity, maturity, diversity, risk, and intent alignment. The oracle returns only a total score with reasoning, not detailed sub-scores.

## Proposed Solution

Update the oracle scoring framework to:

1. **Parse New EVM Data Structure**:
   - Replace `extractTransactionFeatures()` with `extractWalletFeatures()`
   - Leverage pre-calculated metrics (wallet age, protocol counts, lending ratios)
   - Eliminate manual timestamp parsing and protocol detection

2. **Incorporate Questionnaire into AI Analysis**:
   - Add questionnaire responses to the AI prompt
   - Analyze coherence between stated intent and on-chain behavior
   - Weight creditworthiness based on revenue disclosure, liability transparency

3. **Return Detailed Score Breakdown**:
   - Extend AI output to include 5 sub-scores (0-100 each)
   - Map to frontend expectations: `activity`, `maturity`, `diversity`, `riskBehavior`, `surveyMatch`
   - Provide fallback breakdowns when AI unavailable

## User Impact

**Frontend Users:**
- See meaningful score breakdowns based on actual analysis (not random numbers)
- Understand how questionnaire responses influence their reputation score
- View creditworthiness assessment incorporating both on-chain and stated intent

**Developers:**
- API response extended with `metadata.scoreBreakdown` object
- Backward compatible (signature format unchanged, metadata optional)
- Robust fallback handling for missing questionnaire or AI failure

**Protocols Using Reputa:**
- More sophisticated risk assessment combining behavior and self-declared financials
- Differentiate between transaction activity (on-chain) and creditworthiness (questionnaire)
- Better signal for lending decisions

## Technical Approach

### Data Flow Changes

**Current Flow:**
```
n8n EVM endpoint → extractTransactionFeatures() → AI prompt (EVM only)
                                                       ↓
                                        {score, reasoning, risk_factors}
                                                       ↓
Frontend: random scoreBreakdown generation
```

**Proposed Flow:**
```
n8n EVM endpoint (NEW FORMAT) → extractWalletFeatures()
                                         ↓
                                 Rich metrics (age, protocols, lending, tokens)
                                         +
                                 Questionnaire (intent, revenue, liabilities)
                                         ↓
                            Enhanced AI prompt with both data sources
                                         ↓
                      {score, scoreBreakdown, reasoning, risk_factors}
                                         ↓
                            Frontend: display real breakdowns
```

### Key Design Decisions

1. **Generic Questionnaire Handling**
   - Don't hardcode question IDs or specific formats
   - Format as `Q1: <question>\nA1: <answer>` for AI readability
   - Handle empty/missing questionnaires gracefully

2. **Score Breakdown Mapping**
   - Frontend expects: `activity`, `maturity`, `diversity`, `riskBehavior`, `surveyMatch`
   - `activity` ← transaction count, frequency, recent engagement
   - `maturity` ← account age, usage consistency
   - `diversity` ← protocol count, token diversification, unique counterparties
   - `riskBehavior` ← liquidations, concentration risk, liability disclosure
   - `surveyMatch` ← coherence between questionnaire and on-chain behavior

3. **AI Prompt Structure**
   - Section 1: On-Chain Activity (wallet metadata, DeFi, lending, tokens, NFTs)
   - Section 2: Borrower Profile (formatted questionnaire Q&A)
   - Section 3: Scoring Instructions (5 dimensions with specific criteria)
   - Output: JSON with total score + breakdown

4. **Fallback Strategy**
   - If questionnaire empty: Score based on EVM only, set surveyMatch=50 (neutral)
   - If AI fails: Use simple formula + proportional breakdown
   - If breakdown missing: Generate from total score

5. **Backward Compatibility**
   - BCS signature format unchanged (only total score on-chain)
   - `metadata.scoreBreakdown` added (optional, not signed)
   - GET /score continues to work (no questionnaire required)

## Scope

### In Scope (This Change)
- Update `extractWalletFeatures()` to parse new EVM data structure
- Add `formatQuestionnaireForAI()` helper function
- Enhance AI prompt with questionnaire section and breakdown scoring criteria
- Parse `scoreBreakdown` from AI response with validation
- Update POST /score handler to pass questionnaire and return breakdown
- Remove random score generation in frontend `Analyzing.tsx`
- Update frontend TypeScript interfaces for new response structure
- Comprehensive validation tests (curl, end-to-end, edge cases)

### Out of Scope (Future Work)
- NLP extraction of structured data from questionnaire (amounts, entity types)
- Questionnaire UI improvements (tooltips, validation)
- Score history tracking over time
- Comparative scoring (peer percentiles)
- Custom scoring weights per protocol
- Fine-tuned model on DeFi lending outcomes

## Dependencies

**Required Changes:**
- Oracle: `oracle/app/src/index.js` (feature extraction, AI scoring, endpoint handler)
- Frontend: `frontend/src/pages/Analyzing.tsx` (remove random scores, parse API)
- Frontend: `frontend/src/lib/api.ts` (update TypeScript interfaces)

**External Dependencies:**
- n8n webhook API: Must return new data structure
- Ollama LLM: Must support extended prompt (increase `num_predict` to 800 tokens)

**Specification Dependencies:**
- Builds on `integrate-ai-scoring-ollama` change (requires Ollama infrastructure)
- Frontend expects scoreBreakdown structure (must match interface)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| EVM endpoint returns unexpected format | Feature extraction fails | Validate structure, provide defaults for missing fields |
| AI doesn't return breakdown | Frontend shows fallback scores | Generate proportional breakdown from total score |
| Questionnaire contains prompt injection | AI manipulation | Sanitize input, use structured JSON format, low temperature |
| Extended prompt increases latency | Poor UX | Increase token limit, optimize prompt, monitor response times |
| Empty questionnaire crashes scoring | Service outage | Default to "Not provided", score based on EVM only |
| Breakdown scores don't sum correctly | User confusion | Validate 0-100 range, document that they're independent dimensions |

## Success Criteria

**Functional:**
- [ ] Oracle parses new EVM data structure without errors
- [ ] Questionnaire responses included in AI analysis
- [ ] API returns `metadata.scoreBreakdown` with 5 numeric values (0-100)
- [ ] Frontend displays non-random breakdown scores
- [ ] Empty questionnaire doesn't crash (neutral surveyMatch score)
- [ ] Signature verification unchanged (blockchain contract works)

**Quality:**
- [ ] Same address + different questionnaires → different riskBehavior/surveyMatch
- [ ] Liquidation history → lower riskBehavior score
- [ ] High protocol diversity → higher diversity score
- [ ] AI-generated breakdowns are reasonable (not all 100s or 0s)

**Performance:**
- [ ] API response time < 10 seconds
- [ ] Ollama handles extended prompt (800 tokens)
- [ ] No increase in error rate
- [ ] Health checks remain green

**Compatibility:**
- [ ] GET /score continues to work (no questionnaire)
- [ ] Old frontend versions don't break (ignore new fields)
- [ ] BCS signature format unchanged

## Open Questions

1. Should we log when AI scoring falls back to simple calculation?
2. Do we need separate score weights for different protocol use cases (lending vs staking)?
3. Should empty questionnaire answers be treated differently than missing questionnaire?
4. Is 800 token limit sufficient for extended AI response?

## Timeline Estimate

Not providing time estimates per project guidelines. Work broken into verifiable tasks with clear acceptance criteria.
