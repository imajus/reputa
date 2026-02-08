# Tasks: Add Prompt Versioning and A/B Testing Framework to Oracle

## Setup Tasks

- [ ] Create oracle/app/src/prompts.js module
- [ ] Extract current prompt to PROMPT_V1 constant
- [ ] Define prompt version structure (version, hash, template)
- [ ] Implement hash computation for prompt templates
- [ ] Set ACTIVE_PROMPT to current version

## Integration Tasks

- [ ] Update oracle/app/src/index.js to import prompts module
- [ ] Replace inline prompt with ACTIVE_PROMPT.template()
- [ ] Add prompt_version and prompt_hash to API response metadata
- [ ] Ensure metadata is not signed (remains unsigned as before)
- [ ] Test backward compatibility (old responses still work)

## Evaluation Framework Tasks

- [ ] Create oracle/app/scripts/eval-prompts.js script
- [ ] Implement loadSamples() to read .evals/input/*.json files
- [ ] Implement runScoringWithPrompt() to execute scoring with specific prompt
- [ ] Implement consistency calculation (mean, std dev across 10 runs)
- [ ] Implement comparison logic (compare two prompt versions)
- [ ] Generate markdown report with metrics table
- [ ] Add command line arguments for flexible testing

## A/B Testing Tasks

- [ ] Implement selectPrompt() function for gradual rollout
- [ ] Use wallet address for deterministic A/B split
- [ ] Add rolloutPct configuration parameter
- [ ] Log which prompt version used in each request
- [ ] Add A/B testing documentation to README

## Benchmark Tasks

- [ ] Create oracle/app/scripts/benchmark.js for consistency testing
- [ ] Load samples from .evals/input/
- [ ] Run baseline (current prompt) benchmark
- [ ] Run improved prompt benchmark
- [ ] Compare consistency metrics (std dev, schema compliance)
- [ ] Output comparison report

## Testing Tasks

- [ ] Test prompt module loads correctly
- [ ] Test hash computation is stable
- [ ] Test ACTIVE_PROMPT can be changed without breaking API
- [ ] Test A/B split logic distributes fairly (10% to new version)
- [ ] Test metadata includes prompt version and hash
- [ ] Test evaluation script with sample data

## Documentation Tasks

- [ ] Document prompt versioning strategy in oracle/CLAUDE.md
- [ ] Add examples of adding new prompt versions
- [ ] Document A/B testing procedure
- [ ] Document evaluation metrics and interpretation
- [ ] Add prompt change checklist (version, evaluate, test, rollout)
