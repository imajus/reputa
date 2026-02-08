# Proposal: Add Chain-of-Thought Reasoning to Oracle AI Scoring

## Problem Statement

The oracle's AI currently generates scores in a single step without showing intermediate reasoning:

1. **Black Box Scoring**: Users see final scores but not the step-by-step logic
2. **No Self-Verification**: AI doesn't check its own work for consistency
3. **Reduced Accuracy**: Research shows chain-of-thought (CoT) improves accuracy for multi-step reasoning tasks
4. **Limited Auditability**: Difficult to debug why specific scores were assigned

This leads to:
- Lower trust in AI scores (users don't understand "why")
- Missed errors in AI logic (e.g., contradictory reasoning)
- Suboptimal score quality (single-pass generation less accurate than step-by-step)

## Proposed Solution

Implement chain-of-thought reasoning with self-verification:

1. **Step-by-Step Scoring**: Request explicit reasoning for each of 5 dimensions before final scores
2. **Intermediate Reasoning Field**: Add `intermediate_reasoning` array to JSON schema
3. **Self-Verification**: Add verification step where AI checks formula consistency
4. **Shadow Mode First**: Deploy in shadow mode (log outputs without affecting production) to validate before full rollout

Example CoT structure:
```
For each dimension:
1. Consider relevant factors (state what you're analyzing)
2. Explain your scoring logic (show your work)
3. Assign score (0-100)

After all dimensions:
1. Calculate total using weighted formula
2. Verify it matches stated total
3. Check for contradictions in reasoning
```

## User Impact

**Protocol Users:**
- Transparent scoring (see why each dimension was scored)
- Higher quality scores (CoT improves multi-step reasoning)
- Better trust (auditable reasoning trail)

**Developers:**
- Debugging aid (see where AI logic went wrong)
- Quality assurance (can review reasoning for correctness)
- Enhanced metadata for display (show reasoning to end users if desired)

**Oracle Operators:**
- Fewer score disputes (users understand rationale)
- Easier manual review (intermediate steps visible)
- Potential for automated quality checks (verify reasoning consistency)

## Technical Approach

### Chain-of-Thought Prompt Structure

```javascript
const COT_PROMPT = `
## Scoring Instructions

For each dimension, provide step-by-step reasoning:

### 1. Transaction Activity (0-100)
**Consider:** Total transactions (${features.totalTransactions}), avg/month (${features.avgTxsPerMonth})
**Reasoning:** [Explain how you evaluate activity level]
**Score:** [0-100]

### 2. Account Maturity (0-100)
**Consider:** Wallet age (${features.walletAge} days)
**Reasoning:** [Explain how age affects creditworthiness]
**Score:** [0-100]

[Repeat for diversity, riskBehavior, surveyMatch]

### Final Verification
**Calculate total:** (activity×2 + maturity×2 + diversity×2 + riskBehavior×2.5 + surveyMatch×1.5) / 10
**Verify:** Does this match your stated total score?
**Check:** Any contradictions in your reasoning?

Output JSON with intermediate_reasoning array.
`;
```

### Extended JSON Schema

```javascript
const SCHEMA_WITH_COT = {
  ...AI_RESPONSE_SCHEMA,
  properties: {
    ...AI_RESPONSE_SCHEMA.properties,
    intermediate_reasoning: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          dimension: { type: 'string' },
          factors_considered: { type: 'string' },
          reasoning: { type: 'string' },
          score: { type: 'integer', minimum: 0, maximum: 100 }
        },
        required: ['dimension', 'reasoning', 'score']
      },
      minItems: 5,
      maxItems: 5
    },
    verification_passed: { type: 'boolean' }
  },
  required: [...AI_RESPONSE_SCHEMA.required, 'intermediate_reasoning', 'verification_passed']
};
```

### Shadow Mode Implementation

```javascript
// In scoring endpoint
const cotResult = await generateWithChainOfThought(evmData, questionnaire);
const standardResult = await generateAIScore(evmData, questionnaire);

// Log CoT result for analysis (don't use for production yet)
console.log('[SHADOW MODE] CoT result:', JSON.stringify(cotResult));

// Return standard result to client
return standardResult;
```

### Token Budget Impact

- **Current prompt**: ~400-500 tokens
- **CoT instructions**: +200-300 tokens
- **CoT output**: +300-400 tokens (intermediate reasoning)
- **Total**: ~900-1200 tokens
- **Challenge**: Exceeds current `num_predict: 800` budget

**Mitigation:**
- Increase `num_predict` to 1500 (llama3.2:1b can handle it)
- Use more concise CoT format
- Deploy only after validating token budget in shadow mode

### Dependencies

- No new dependencies

### Performance Impact

- **Latency increase**: +2-4s (more tokens to generate)
- **Expected total**: 5-12s per request
- **Budget compliance**: Still under 15s acceptable limit, but closer to edge
- **Quality improvement**: Research shows 10-30% accuracy improvement with CoT

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token budget exceeded | Truncated responses | Increase num_predict to 1500; monitor output length |
| Latency too high | Poor UX | Shadow mode first; optimize prompt if needed |
| CoT overhead not worth it | Wasted resources | A/B test: compare CoT vs non-CoT accuracy |
| Reasoning quality poor | Garbage output | Use validation + retry from schema validation change |

## Success Metrics

- **Accuracy improvement**: Score consistency improves (std dev reduces by >10%)
- **Self-verification rate**: >95% of responses pass internal verification
- **Latency acceptable**: P95 stays under 12s
- **Quality assessment**: Manual review shows reasoning is logical and consistent
- **No regressions**: Schema compliance remains >95%

## Deployment Strategy

### Phase 1: Shadow Mode (Week 1)
- Deploy CoT alongside standard scoring
- Log all CoT outputs
- Compare 100 real requests side-by-side
- Analyze: consistency, quality, latency

### Phase 2: Evaluation (Week 2)
- Review shadow mode data
- Measure metrics vs baseline
- Decide: proceed to production or iterate

### Phase 3: Production Rollout (Week 3)
- If metrics positive, enable for 10% traffic via A/B testing
- Monitor for regressions
- Gradually increase to 100%

### Rollback Plan
- If latency exceeds 15s or quality degrades, instant rollback to standard prompt
- Shadow mode always available for debugging

## Related Changes

- **Depends on** `add-json-schema-validation-oracle`: Extended schema validation needed
- **Depends on** `add-prompt-versioning-oracle`: CoT as separate prompt version
- **Complements** `add-few-shot-prompting-oracle`: Can combine CoT with examples
- **Independent** of `add-deterministic-seeding-oracle`: Both improve quality differently

## Alternative: CoT for Edge Cases Only

If full CoT proves too slow, consider hybrid approach:
- Use standard scoring by default
- Trigger CoT only when:
  - Schema validation fails on first attempt
  - Score mismatch detected
  - User explicitly requests detailed reasoning (new API parameter)

This limits latency impact while preserving quality improvement for problematic cases.
