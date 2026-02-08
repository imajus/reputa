# Proposal: Add Few-Shot Prompting to Oracle AI Scoring

## Problem Statement

The oracle's AI prompt currently uses zero-shot learning - it provides instructions and schema but no examples of correct outputs. This leads to:

1. **Inconsistent Reasoning Patterns**: The AI may interpret scoring criteria differently across requests
2. **Suboptimal Score Distribution**: Without reference points, scores may cluster or drift
3. **Missed Scoring Nuances**: The AI doesn't see how to balance multiple factors (e.g., high activity but recent liquidation)

Research shows few-shot prompting improves scoring consistency by 12.6% by providing the model with concrete examples of correct behavior.

## Proposed Solution

Add 2-3 hand-crafted example wallet analyses to the AI prompt covering:

1. **High-Reputation Example** (~800-900 score):
   - Mature account (1200+ days)
   - High transaction volume
   - Diverse protocol usage
   - Zero liquidations
   - Healthy borrow/repay ratio

2. **Medium-Reputation Example** (~400-600 score):
   - Moderate account age (300-600 days)
   - Moderate activity
   - Limited protocol diversity
   - Some liquidations
   - Mixed questionnaire alignment

3. **Low-Reputation Example** (~100-300 score):
   - New account (<100 days)
   - Low activity
   - Single protocol
   - Recent liquidations or high risk behavior
   - Poor questionnaire alignment

Each example shows:
- Input features (wallet age, transactions, protocols, lending history)
- Expected JSON output with scores and reasoning
- Rationale demonstrating scoring criteria application

## User Impact

**Protocol Users:**
- More consistent scores for similar wallet profiles
- Better calibrated risk assessment across the scoring range
- Clearer understanding of what drives high vs low scores

**Developers:**
- Reduced retry rate (better first-attempt accuracy)
- More predictable AI behavior
- Easier debugging (examples serve as documentation)

**Oracle Operators:**
- Lower variance in scores for similar wallets
- Fewer edge cases requiring manual review
- Improved AI quality without model changes

## Technical Approach

### Example Structure

```javascript
const SCORING_EXAMPLES = `
## Example 1: High-Reputation Wallet

### Input Features
- Wallet Age: 1200 days
- Total Transactions: 850
- Average Txs/Month: 21
- Unique Counterparties: 145
- Protocols Used: 8 (Aave, Uniswap V3, Curve, Morpho Blue, Compound V3)
- Borrow Count: 12
- Repay Count: 15
- Liquidation Count: 0
- Borrow/Repay Ratio: 1.25 (healthy overpayment)
- Token Diversity: 15 tokens
- Concentration Risk: Low (0.3)
- ETH Balance: 2.5 ETH

### Questionnaire Summary
- Wallet Control: "Personal wallet, sole control"
- Loan Purpose: "Yield farming and liquidity provision"
- Revenue Streams: "Trading profits, staking rewards"
- Liabilities: "Disclosed all existing loans on Aave"

### Expected Output
{
  "score": 820,
  "scoreBreakdown": {
    "activity": 85,
    "maturity": 90,
    "diversity": 80,
    "riskBehavior": 92,
    "surveyMatch": 75
  },
  "reasoning": "Mature account with consistent activity across multiple DeFi protocols and zero liquidation history. Strong repayment behavior with 25% over-repayment ratio.",
  "risk_factors": [],
  "strengths": [
    "Excellent repayment history (15 repays, 0 liquidations)",
    "Diverse protocol usage across 8 platforms",
    "Long account age (3.3 years) with consistent activity"
  ]
}

[Examples 2 and 3 follow similar structure]
`;
```

### Integration Point

Insert examples into prompt after instructions but before actual wallet data:

```javascript
const prompt = `
${INSTRUCTIONS}

${SCORING_EXAMPLES}

## Your Task

Now analyze the following wallet...
${actualWalletData}
`;
```

### Token Budget

- **Example overhead**: ~300-400 tokens (3 examples × ~100-130 tokens each)
- **Current prompt**: ~400-500 tokens
- **New total**: ~700-900 tokens
- **Budget**: 800 token num_predict limit (fits comfortably)
- **Latency impact**: +0.5-1s for longer context

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Examples bias AI toward example scores | Scores cluster near examples | Use diverse range (low/med/high) |
| Token budget exceeded | Truncated responses | Keep examples concise, monitor length |
| Examples become outdated | Drift from current data patterns | Version examples with prompts, periodic review |
| Increased latency | Slower responses | Acceptable (+0.5-1s, staying under 10s budget) |

## Success Metrics

- **Consistency improvement**: Std dev of scores for same wallet reduced by >10%
- **Score distribution**: Healthy spread across 0-1000 range (not clustered)
- **First-attempt success**: Schema compliance rate increases (fewer retries needed)
- **Reasoning quality**: Manual review shows better alignment with criteria

## Related Changes

- Complements `add-json-schema-validation-oracle`: Better examples reduce retry needs
- Complements `add-prompt-versioning-oracle`: Examples versioned alongside prompts
- Independent of `add-deterministic-seeding-oracle`: Can implement in any order
