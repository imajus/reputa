# Tasks: Add Chain-of-Thought Reasoning to Oracle AI Scoring

## Design Tasks

- [ ] Design chain-of-thought prompt structure
- [ ] Write step-by-step instructions for each dimension
- [ ] Add self-verification section to prompt
- [ ] Determine optimal token budget (test 1200 vs 1500)
- [ ] Design intermediate_reasoning schema structure
- [ ] Plan shadow mode deployment strategy

## Implementation Tasks

- [ ] Extend JSON schema to include intermediate_reasoning array
- [ ] Add verification_passed boolean to schema
- [ ] Create generateWithChainOfThought() function
- [ ] Implement CoT prompt template
- [ ] Increase num_predict to 1500 (from 800)
- [ ] Add shadow mode logic (run CoT + standard, return standard)
- [ ] Log CoT results for analysis
- [ ] Preserve backward compatibility (metadata only)

## Shadow Mode Tasks

- [ ] Deploy shadow mode to production
- [ ] Collect 100 real request comparisons
- [ ] Log both CoT and standard results
- [ ] Monitor latency distribution (P50, P95, P99)
- [ ] Track token usage per request
- [ ] Measure self-verification pass rate

## Analysis Tasks

- [ ] Compare consistency: CoT vs standard (std dev)
- [ ] Compare accuracy: manual review of 20 samples
- [ ] Compare latency: measure impact
- [ ] Analyze reasoning quality (coherence, relevance)
- [ ] Check for token truncation issues
- [ ] Identify failure modes

## Testing Tasks

- [ ] Test CoT prompt generates valid JSON
- [ ] Test intermediate_reasoning has 5 items
- [ ] Test verification logic catches contradictions
- [ ] Test with sample data from .evals/input/*.json
- [ ] Measure token count for various wallet profiles
- [ ] Test retry logic with extended schema

## Optimization Tasks (if needed)

- [ ] Compress prompt if token budget tight
- [ ] Optimize intermediate_reasoning format
- [ ] Consider hybrid approach (CoT only for edge cases)
- [ ] Tune num_predict to minimum viable value

## Validation Tasks

- [ ] Verify latency P95 < 15s
- [ ] Verify consistency improvement >10%
- [ ] Verify self-verification rate >95%
- [ ] Verify no schema compliance regression
- [ ] Verify backward compatibility maintained

## Rollout Tasks

- [ ] Evaluate shadow mode results
- [ ] Make go/no-go decision
- [ ] If approved: create CoT prompt as new version
- [ ] Enable for 10% traffic via A/B testing
- [ ] Monitor metrics for 48 hours
- [ ] Gradually increase to 100% or rollback

## Documentation Tasks

- [ ] Document CoT prompt structure
- [ ] Explain self-verification mechanism
- [ ] Add shadow mode logs location
- [ ] Document rollback procedure
- [ ] Update oracle/CLAUDE.md with CoT behavior
