# Tasks: Add Few-Shot Prompting to Oracle AI Scoring

## Design Tasks

- [ ] Research representative wallet profiles from production data
- [ ] Design 3 example wallets covering score ranges (low/medium/high)
- [ ] Write high-reputation example (800-900 score range)
- [ ] Write medium-reputation example (400-600 score range)
- [ ] Write low-reputation example (100-300 score range)
- [ ] Ensure examples demonstrate all 5 scoring dimensions
- [ ] Validate examples match documented weighting formula

## Implementation Tasks

- [ ] Create SCORING_EXAMPLES constant in oracle/app/src/index.js
- [ ] Format examples with clear input/output structure
- [ ] Integrate examples into prompt construction
- [ ] Position examples after instructions, before actual wallet data
- [ ] Verify token count stays within 800 num_predict budget
- [ ] Add comment documenting example versioning strategy

## Testing Tasks

- [ ] Test prompt with examples generates valid responses
- [ ] Measure consistency: run same wallet 10 times, check std dev
- [ ] Compare with baseline (no examples): measure improvement
- [ ] Verify examples don't cause score clustering
- [ ] Test across diverse wallet profiles from .evals/input/*.json
- [ ] Measure latency impact (should be +0.5-1s)

## Validation Tasks

- [ ] Verify examples are factually accurate and realistic
- [ ] Ensure examples cover edge cases (liquidations, low activity, questionnaire mismatch)
- [ ] Check reasoning in examples aligns with scoring criteria
- [ ] Validate score breakdown matches total score in examples
- [ ] Confirm no hardcoded biases introduced

## Documentation Tasks

- [ ] Document example selection rationale
- [ ] Add versioning metadata to examples
- [ ] Update oracle/CLAUDE.md with few-shot approach
- [ ] Note token budget allocation for future prompt changes
