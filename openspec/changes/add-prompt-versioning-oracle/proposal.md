# Proposal: Add Prompt Versioning and A/B Testing Framework to Oracle

## Problem Statement

The oracle's AI prompt is currently hardcoded inline without version control or testing infrastructure:

1. **No Version Tracking**: Prompt changes are buried in git commits without semantic versioning
2. **No A/B Testing**: Can't scientifically compare prompt improvements before full rollout
3. **No Prompt Metadata**: Responses don't indicate which prompt version generated them (debugging difficulty)
4. **No Evaluation Framework**: No tooling to measure prompt quality improvements objectively

This leads to:
- Risk of prompt regressions going unnoticed
- Inability to iterate safely on prompt improvements
- Difficulty debugging production issues ("which prompt version caused this?")
- No data-driven decisions on prompt changes

## Proposed Solution

Implement prompt versioning and A/B testing framework:

1. **Prompt Module**: Extract prompts to `oracle/app/src/prompts.js` with semantic versioning
2. **Prompt Metadata**: Include version hash in API response metadata (unsigned, for debugging)
3. **Evaluation Script**: Create `oracle/app/scripts/eval-prompts.js` to compare prompt versions
4. **Benchmark Framework**: Use existing `.evals/input/sample-*.json` files for reproducible testing
5. **A/B Testing Support**: Enable gradual rollout (10% traffic to new prompt before 100%)

## User Impact

**Protocol Users:**
- Higher quality prompts (scientifically validated before deployment)
- More stable scoring (regressions caught in evaluation)
- Transparent versioning (metadata shows prompt version used)

**Developers:**
- Easy prompt iteration (change one file, not inline strings)
- Data-driven improvements (compare metrics before rollout)
- Better debugging (prompt hash in logs identifies version)

**Oracle Operators:**
- Safe prompt deployment (A/B test on subset before full rollout)
- Audit trail (version history in git + metadata)
- Performance tracking (consistency, quality metrics per version)

## Technical Approach

### Prompt Module Structure

```javascript
// oracle/app/src/prompts.js
import { createHash } from 'crypto';

export const PROMPT_V1 = {
  version: '1.0.0',
  hash: null, // Computed on load
  template: (features, questionnaire) => {
    return `You are a DeFi creditworthiness analyzer...
    [original prompt content]
    `;
  }
};

export const PROMPT_V2 = {
  version: '2.0.0',
  hash: null,
  template: (features, questionnaire) => {
    return `You are a DeFi creditworthiness analyzer...
    [improved prompt with few-shot examples]
    `;
  }
};

// Compute hashes
for (const prompt of [PROMPT_V1, PROMPT_V2]) {
  const templateStr = prompt.template.toString();
  prompt.hash = createHash('sha256').update(templateStr).digest('hex').slice(0, 8);
}

export const ACTIVE_PROMPT = PROMPT_V2;
```

### Metadata Integration

```javascript
// In API response
res.json({
  score: aiResult.score,
  wallet_address: address,
  timestamp_ms: timestampMs,
  signature,
  metadata: {
    scoreBreakdown: aiResult.scoreBreakdown,
    reasoning: aiResult.reasoning,
    risk_factors: aiResult.riskFactors,
    strengths: aiResult.strengths,
    features: aiResult.features,
    prompt_version: ACTIVE_PROMPT.version,  // NEW
    prompt_hash: ACTIVE_PROMPT.hash         // NEW
  }
});
```

### Evaluation Script

```javascript
// oracle/app/scripts/eval-prompts.js
import fs from 'fs';
import { PROMPT_V1, PROMPT_V2 } from '../src/prompts.js';

async function evaluatePrompt(prompt, samples) {
  const results = [];
  for (const sample of samples) {
    // Run scoring 10 times per sample
    const scores = [];
    for (let i = 0; i < 10; i++) {
      const result = await runScoringWithPrompt(prompt, sample);
      scores.push(result.score);
    }

    // Calculate consistency (std dev)
    const mean = scores.reduce((a, b) => a + b) / scores.length;
    const variance = scores.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / scores.length;
    const stdDev = Math.sqrt(variance);

    results.push({ sample: sample.address, mean, stdDev, scores });
  }
  return results;
}

// Compare prompts
const samples = loadSamples('.evals/input/');
const v1Results = await evaluatePrompt(PROMPT_V1, samples);
const v2Results = await evaluatePrompt(PROMPT_V2, samples);

// Generate report
console.log('Consistency Improvement:', calculateImprovement(v1Results, v2Results));
```

### A/B Testing

```javascript
// In scoring endpoint
function selectPrompt(walletAddress) {
  // Use last byte of address for deterministic A/B split
  const lastByte = parseInt(walletAddress.slice(-2), 16);
  const rolloutPct = 10; // 10% to new prompt

  if (lastByte < (256 * rolloutPct / 100)) {
    return PROMPT_V2; // New prompt
  }
  return PROMPT_V1; // Stable prompt
}
```

### Dependencies

- No new dependencies (uses existing crypto and fs modules)

### Performance Impact

- **Module load**: One-time overhead at startup (~1ms)
- **Hash computation**: One-time at module load (~5ms)
- **Runtime overhead**: None (function call vs inline string)
- **Metadata overhead**: +50 bytes per response (negligible)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt hash collisions | Wrong version identified | Use 8 chars (1 in 4 billion collision rate) |
| A/B split bias | Certain wallets always get new prompt | Use address-based split (deterministic but fair) |
| Evaluation too slow | Long testing cycles | Parallelize sample evaluation |
| Git conflicts on prompts.js | Merge conflicts | Keep prompts immutable, only change ACTIVE_PROMPT |

## Success Metrics

- **Versioning adoption**: All prompt changes go through versioning
- **A/B testing usage**: New prompts tested on 10% before 100% rollout
- **Regression prevention**: No prompt changes deployed without evaluation
- **Debugging improvement**: Prompt hash in logs enables version tracking

## Related Changes

- **Depends on** `add-few-shot-prompting-oracle`: Version 2.0.0 includes few-shot examples
- **Complements** `add-json-schema-validation-oracle`: Validation works with any prompt version
- **Enables** future chain-of-thought prompts: Easy to version and compare
