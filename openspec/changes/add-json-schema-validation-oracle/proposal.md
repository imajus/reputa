# Proposal: Add JSON Schema Validation and Retry Logic to Oracle

## Problem Statement

The oracle's AI scoring system currently uses basic JSON format enforcement (`format: 'json'`) but lacks robust validation:

1. **No Schema Validation**: After parsing the JSON response, there's no validation that all required fields exist or that values are within expected ranges
2. **No Retry Logic**: If the AI generates an invalid response, the system falls back to simple transaction counting without attempting to get a valid AI score
3. **Manual Clamping**: Scores are manually clamped (0-1000 for total, 0-100 for dimensions) after parsing, catching errors too late
4. **No Cross-Validation**: The system doesn't verify that the total score matches the weighted breakdown formula

This leads to:
- Occasional parsing errors when AI omits required fields
- Acceptance of scores that don't match the documented weighting formula
- Loss of AI scoring quality when simple fallback is used unnecessarily

## Proposed Solution

Implement structured output validation with retry logic:

1. **JSON Schema Definition**: Define formal schema matching expected AI response structure with type and range constraints
2. **Grammar-Level Enforcement**: Pass schema to Ollama via `format` parameter for grammar-based constraint during generation
3. **Runtime Validation**: Use `ajv` library to validate parsed responses against schema
4. **Retry with Temperature Decay**: On validation failure, retry up to 3 times with decreasing temperature (0.3 → 0.2 → 0.1)
5. **Cross-Validation**: Verify total score matches weighted breakdown within 2% tolerance

## User Impact

**Protocol Users:**
- More consistent AI scores (fewer fallbacks to simple counting)
- Higher confidence in score accuracy (verified against formula)
- Better quality reasoning and risk factors

**Developers:**
- Clearer error logging when AI outputs are invalid
- Automatic recovery from transient AI issues
- No changes to API contract (backward compatible)

**Oracle Operators:**
- Reduced fallback rate from ~5% to <1% (estimated based on retry effectiveness)
- Monitoring metrics: schema compliance rate, retry frequency, validation failures

## Technical Approach

### Schema Structure

```javascript
const AI_RESPONSE_SCHEMA = {
  type: 'object',
  properties: {
    score: { type: 'integer', minimum: 0, maximum: 1000 },
    scoreBreakdown: {
      type: 'object',
      properties: {
        activity: { type: 'integer', minimum: 0, maximum: 100 },
        maturity: { type: 'integer', minimum: 0, maximum: 100 },
        diversity: { type: 'integer', minimum: 0, maximum: 100 },
        riskBehavior: { type: 'integer', minimum: 0, maximum: 100 },
        surveyMatch: { type: 'integer', minimum: 0, maximum: 100 }
      },
      required: ['activity', 'maturity', 'diversity', 'riskBehavior', 'surveyMatch']
    },
    reasoning: { type: 'string', minLength: 10, maxLength: 500 },
    risk_factors: { type: 'array', items: { type: 'string' } },
    strengths: { type: 'array', items: { type: 'string' } }
  },
  required: ['score', 'scoreBreakdown', 'reasoning', 'risk_factors', 'strengths']
};
```

### Retry Logic Flow

```
Attempt 1 (temp=0.3):
  Generate → Parse → Schema Valid? → Cross-Valid? → Success
                          ↓ No           ↓ No
Attempt 2 (temp=0.2):
  Generate → Parse → Schema Valid? → Cross-Valid? → Success
                          ↓ No           ↓ No
Attempt 3 (temp=0.1):
  Generate → Parse → Schema Valid? → Cross-Valid? → Success
                          ↓ No           ↓ No
                      Fallback Scoring
```

### Dependencies

- **ajv@8.17.1**: Fast JSON schema validator (~125KB, zero runtime dependencies)
- Compatible with existing Ollama 0.10.1+ structured outputs feature

### Performance Impact

- **Schema validation overhead**: +100-200ms per request
- **Retry overhead**: +3-8s per retry (rarely triggered with grammar enforcement)
- **Expected retry rate**: <5% of requests (most succeed on first attempt)
- **Net latency**: P50 unchanged (~4s), P95 +0.2s (~8.2s), well under 10s budget

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema too strict, frequent retries | High latency | Start with lenient schema, tighten based on data |
| Ajv adds bundle size | Minimal (125KB) | Acceptable for quality improvement |
| Ollama version incompatibility | Schema enforcement fails | Fall back to basic `format: 'json'` if unsupported |
| All retries fail | User gets fallback score | Existing fallback logic preserved |

## Success Metrics

- **Schema compliance rate**: >95% without retries
- **Retry rate**: <5% of requests need retries
- **Fallback rate**: Reduced from current ~5% to <1%
- **Cross-validation pass rate**: >98% of responses match formula
- **Latency P95**: Stays under 10s

## Related Changes

This change is independent but complements:
- `add-few-shot-prompting-oracle`: Better prompts reduce retry needs
- `add-deterministic-seeding-oracle`: Reproducibility for same wallet
- `add-prompt-versioning-oracle`: Track prompt quality improvements
